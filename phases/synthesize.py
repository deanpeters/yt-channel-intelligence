import json
import os
from datetime import datetime

from openai import OpenAI

import db
from config import DATA_DIR, LLM_MODEL, LOOKBACK_MONTHS, OPENAI_API_KEY, REPORTS_DIR

_client = OpenAI(api_key=OPENAI_API_KEY)

_TRANSCRIPT_CHAR_LIMIT = 25_000

_SECTION_ORDER = [
    "product_line",
    "problem_obsession",
    "building_for",
    "how_they_decide",
    "placing_bets",
    "category_framing",
    "momentum_tone",
    "whats_shifted",
    "not_saying",
]

_SECTION_TITLES = {
    "product_line":      "Product line",
    "problem_obsession": "The problem they're obsessed with",
    "building_for":      "Who they're building for",
    "how_they_decide":   "How they decide what to build",
    "placing_bets":      "Where they're placing bets",
    "category_framing":  "How they frame the category",
    "momentum_tone":     "Momentum and tone",
    "whats_shifted":     "What's shifted",
    "not_saying":        "What they're not saying",
}

_PASS1_SYSTEM = """\
You are a product intelligence analyst extracting competitive signal from one video \
transcript for a Product Manager. Return valid JSON with exactly these keys, all present: \
customer_problems, product_philosophy, strategic_bets, market_framing, \
competitive_signals, customer_voices, notable_quotes, product_mentions.

Each key except product_mentions is a list of {statement, quote}. statement is a \
normalized one-liner in your words; quote is verbatim supporting text from the transcript. \
product_mentions is a list of {name, does}.

Rules:
- customer_problems are OUTCOMES customers struggle with, never feature descriptions.
- product_philosophy includes what they refuse to do, not only what they pursue.
- competitive_signals includes tensions they are answering even when no rival is named: \
  defensive pricing language, parity claims, overemphasized differentiation.
- customer_voices is reserved for featured customers speaking — keep it separate from \
  company voice.
- notable_quotes is leadership or founder voice only. Not the narrator. Not a customer.
- If a statement cannot be anchored to a verbatim quote, omit it.
- Return only the JSON object. No preamble, no markdown."""

_PASS2_SYSTEM = """\
You are a strategic advisor preparing a decision-support briefing for a Product Manager \
leader — a coach, trainer, or executive who will use this to make decisions about \
competing against, partnering with, or building training material around this company. \
You have per-video extracted summaries from one company's YouTube channel over a fixed \
lookback window, ordered by date.

Your job is INSIGHTS, not data. The difference:
- Data: "They mentioned the Enso Prime lenses in 6 videos."
- Insight: "They are using the Enso Prime lenses to buy entry into a customer segment \
  they previously priced out — which is either a TAM expansion bet or a defensive hedge \
  against affordable competitors. They don't say which. That ambiguity is itself a signal."

Return a JSON object with exactly two top-level keys:

"executive_summary": A string. 3-4 sentences of STRATEGIC INSIGHT, not company \
description. The reader already knows this company exists. Answer: What is this company \
trying to do that they haven't fully said out loud? What should a PM leader know before \
walking into a room with them, competing against them, or teaching about them? Lead with \
the most surprising or consequential thing in the data. Do not open with the company name \
or describe what they make — product_line covers that.

"sections": An object with exactly these nine section keys in this order: \
product_line, problem_obsession, building_for, how_they_decide, placing_bets, \
category_framing, momentum_tone, whats_shifted, not_saying.

Each section is a list of claims. Each claim has:
- statement: A STRATEGIC INSIGHT. Draw a conclusion. Don't hedge. What does this mean \
  for a PM leader? "They do X" is data. "They do X because they believe Y, which means \
  Z for competitors" is an insight.
- signal_strength: count of DISTINCT videos supporting this statement (integer)
- evidence: list of up to 3 strongest {video, date, quote} anchors

Section guidance:

product_line — EXHAUSTIVE inventory: include EVERY distinct product or product family \
mentioned across all videos. Miss nothing — this is the one section where completeness \
beats selectivity. Statement format: "ProductName — what it does, and what its presence \
in the lineup signals strategically." Signal_strength = distinct videos mentioning it. \
Order by signal_strength descending. If no verbatim quote fits a product, still include \
the product claim with an empty evidence list — do NOT write "No quote" as a placeholder.

problem_obsession — Not just what problem they solve, but WHY this problem — what does \
their obsession with it reveal about their beliefs about the market? One aggregated claim \
with signal_strength 10 beats 10 thin claims with signal_strength 1.

building_for — Name the mindset and JTBD, then state the implication: who they are NOT \
building for, and whether that exclusion is deliberate positioning or a blind spot.

how_they_decide — Surface the principle behind the pattern. "They refuse to do X because \
they believe Y" is an insight. What constraint or belief drives their product decisions?

placing_bets — State the bet AND the belief behind it. What must be true for this bet to \
pay off? If that assumption turns out wrong, what breaks first?

category_framing — Genuine category creation, or reframing to escape competitive \
comparison? What does their framing protect them from having to answer?

momentum_tone — Lead with the verdict: ON OFFENSE or ON DEFENSE, and what proves it. \
Then: what does the tone reveal about what they are worried about but won't say?

whats_shifted — What changed between early-window and late-window content? Name what \
disappeared and what appeared. State what the DIRECTION of that shift signals about \
where they are headed next.

not_saying — Most valuable section. For each gap: name the absence, explain what a \
company in this category would normally say, and state the strategic implication — \
vulnerability, deliberate positioning, or signal of something unannounced? Thin evidence \
is expected; carry the reasoning in the statement.

Aggregation rules:
- Collapse aggressively. Theme across 15 videos = ONE claim with signal_strength 15, \
  not 15 claims with signal_strength 1.
- For evidence quotes, use VERBATIM text from the quote fields only — never a statement \
  (normalized analyst summary). Omit an evidence item rather than paraphrase.
- momentum_tone and not_saying claims may have no evidence — the statement carries \
  the strategic reasoning.

No preamble, no markdown, return only the JSON."""


def run(company_slug: str, conn) -> str:
    """Run both synthesis passes. Returns the path to the finished report."""
    _pass1_analyze(conn)
    return _pass2_synthesize(company_slug, conn)


def _pass1_analyze(conn) -> None:
    videos = db.get_videos_below_status(conn, "analyzed")
    to_analyze = [v for v in videos if v["status"] == "transcribed"]

    if not to_analyze:
        print("All videos already analyzed.")
        return

    print(f"Analyzing {len(to_analyze)} video(s)...")
    completed = 0

    for video in to_analyze:
        video_id = video["video_id"]

        try:
            with open(video["transcript_path"], encoding="utf-8") as f:
                transcript = f.read().strip()
        except OSError as e:
            print(f"  Skipping {video_id}: {e}")
            continue

        if not transcript:
            print(f"  Skipping {video_id}: empty transcript")
            continue

        try:
            response = _client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": _PASS1_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"Video title: {video['title']}\n\n"
                            f"Transcript:\n{transcript[:_TRANSCRIPT_CHAR_LIMIT]}"
                        ),
                    },
                ],
                response_format={"type": "json_object"},
            )
            summary_json = response.choices[0].message.content
            json.loads(summary_json)  # validate before storing
        except Exception as e:
            print(f"  Skipping {video_id}: {e}")
            continue

        db.set_status(conn, video_id, "analyzed", summary_json=summary_json)
        completed += 1
        print(f"  Analyzed {completed}/{len(to_analyze)}: {video['title'][:60]}")

    print(f"Analysis complete: {completed}/{len(to_analyze)} succeeded.")


def _pass2_synthesize(company_slug: str, conn) -> str:
    rows = conn.execute(
        "SELECT title, published, summary_json FROM videos "
        "WHERE status = 'analyzed' AND summary_json IS NOT NULL "
        "ORDER BY published"
    ).fetchall()

    if not rows:
        raise RuntimeError("No analyzed videos to synthesize.")

    summaries_block = "\n\n".join(
        f"### {row['title']} ({row['published']})\n{row['summary_json']}"
        for row in rows
    )

    print(f"Synthesizing report from {len(rows)} video(s)...")

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _PASS2_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Company: {company_slug}\n"
                    f"Videos analyzed: {len(rows)}\n\n"
                    f"{summaries_block}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    canvas_data = json.loads(response.choices[0].message.content)

    run_date = datetime.now().strftime("%Y-%m-%d")

    canvas = {
        "meta": {
            "company_slug": company_slug,
            "run_date": run_date,
            "lookback_months": LOOKBACK_MONTHS,
            "video_count": len(rows),
            "model": LLM_MODEL,
        },
        "executive_summary": canvas_data.get("executive_summary", ""),
        "sections": canvas_data.get("sections", {}),
    }

    # Save machine canvas to .workspace
    canvas_dir = os.path.join(DATA_DIR, company_slug)
    os.makedirs(canvas_dir, exist_ok=True)
    canvas_path = os.path.join(canvas_dir, f"canvas-{run_date}.json")
    with open(canvas_path, "w", encoding="utf-8") as f:
        json.dump(canvas, f, indent=2)

    # Render human report from canvas
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"{company_slug}-{run_date}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(_render_report(canvas))

    return report_path


def _render_report(canvas: dict) -> str:
    meta = canvas["meta"]
    sections = canvas.get("sections", {})
    exec_summary = canvas.get("executive_summary", "")

    lines = [
        f"# Channel Intelligence: {meta['company_slug']}",
        "",
        f"*{meta['run_date']} · {meta['video_count']} videos · {meta['lookback_months']}-month window*",
        "",
    ]

    if exec_summary:
        lines += [exec_summary, ""]

    lines += ["---", ""]

    for key in _SECTION_ORDER:
        title = _SECTION_TITLES[key]
        claims = sections.get(key, [])

        lines.append(f"## {title}")
        lines.append("")

        if not claims:
            lines.append("*No signal found in this window.*")
            lines.append("")
        else:
            for claim in claims:
                statement = claim.get("statement", "")
                signal = claim.get("signal_strength", 0)
                evidence = claim.get("evidence", [])

                lines.append(
                    f"**{statement}**"
                    + (f" *(signal: {signal} video{'s' if signal != 1 else ''})*" if signal else "")
                )
                lines.append("")

                for e in evidence:
                    quote = e.get("quote", "").strip()
                    video = e.get("video", "")
                    date = e.get("date", "")
                    if quote and not quote.lower().startswith("no quote"):
                        lines.append(f"> \"{quote}\"")
                        attr = " · ".join(filter(None, [video, date]))
                        if attr:
                            lines.append(f"> — *{attr}*")
                        lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)
