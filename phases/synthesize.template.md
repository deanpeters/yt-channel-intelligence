# synthesize.template.md — Channel Intelligence synthesis spec

Handoff spec for the synthesis phase. Defines what Pass 1 extracts per video, what
Pass 2 assembles per company, and the output contract that makes one company's canvas
comparable against another's. Build `synthesize.py` to this. Field names are normative —
do not improvise alternates.

## Why this shape

The job is competitive intelligence for a Product Manager, and intelligence is only
useful if it stacks. Three rules make a report comparable:

1. **Fixed slots.** Every company fills the same nine sections in the same order, plus an
   executive summary. Same shape side by side is what lets you diff Company A against
   Company B, or one company against itself across run dates.
2. **Anchored evidence.** Every claim carries the video and quote it came from, so a
   Product Manager can trust and trace it instead of taking prose on faith.
3. **Two layers.** The executive summary (who they are, what they make, where they're
   headed) grounds the reader before the nine analytical sections. Neither layer is
   useful without the other.

Free-form prose gives neither comparability nor traceability. So Pass 2 emits a structured
canvas first, then renders the readable report from it. The prose is the face; the
structured object is what the compare step actually reads.

## Design decisions baked in

- **Pass 1 carries eight keys**: the seven strategic extractors plus a flat
  `product_mentions` inventory. Strategy-first, but the literal "what do they ship"
  list survives because competitive intel sometimes needs the plain enumeration.
- **`product_line` in Pass 2 is synthesized from all `product_mentions`.** Pass 1
  collects them per-video; Pass 2 aggregates them into a structured product inventory with
  signal strength. A product mentioned in 12 videos should show signal 12, not 12
  separate one-video claims.
- **`momentum_tone` is a distinct section, not a modifier.** Offense/defense,
  confident/hedging, accelerating/consolidating — these are intelligence in their own right
  and belong in a named, traceable slot, not as a color comment on other sections.
- **`notable_quotes` is leadership/founder voice only.** Featured-customer language
  lives in its own bucket (`customer_voices`) so it never gets blended into the
  company's own marketing register. Customer words are the least-spun text in the corpus.
- **"Who they're building for" has no Pass 1 feeder by design.** Pass 2 reconstructs the
  archetype from `customer_problems` + `customer_voices`. The job reveals the user; we
  don't assert demographics. Escape hatch in Open TODOs if it comes out mushy.
- **"What they're not saying" is not an aggregation.** Absence isn't in the transcripts.
  Pass 2 must reason about what a company in this category normally says and flag the
  gaps. This is the highest-signal section and the easiest to get wrong.

---

## Pass 1 — per-video extraction

Input: one transcript + video title. Output: one JSON object, these eight keys, every key
present (empty list if nothing found).

```yaml
customer_problems:    # outcomes customers struggle with, NOT features
  - statement: "normalized one-line problem in your words"
    quote: "verbatim line from transcript that supports it"
product_philosophy:   # why/how they build: craft, speed, tradeoffs, what they WON'T do
  - statement: "..."
    quote: "..."
strategic_bets:       # where they're doubling down, new directions, what they move toward
  - statement: "..."
    quote: "..."
market_framing:       # how they define/reframe the category — new space or someone else's game
  - statement: "..."
    quote: "..."
competitive_signals:  # tensions they answer, NAMED OR NOT — defensive pricing, parity claims,
  - statement: "..."  # differentiation overemphasis. Capture the unnamed ones especially.
    quote: "..."
customer_voices:      # when a customer is featured, the problem/outcome in THEIR words
  - statement: "..."
    quote: "..."
notable_quotes:       # LEADERSHIP/FOUNDER voice only — not narrator, not customer
  - statement: "why this quote matters"
    quote: "..."
product_mentions:     # flat inventory — product or feature name + one-line what-it-does
  - name: "..."
    does: "..."
```

### Pass 1 extraction rules

- `quote` must be verbatim from the transcript. If you can't anchor a statement to a real
  quote, don't emit the item. No quote, no claim.
- Do **not** put `video_id` or `date` inside items. The database row already carries them;
  Pass 2 joins them back. Keep items to the shape above.
- One transcript can be long. Honor the existing `_TRANSCRIPT_CHAR_LIMIT` truncation.
- Deduplicate within a video. Same point made three times in one video is one item.

### Pass 1 system prompt

```
You are a product intelligence analyst extracting competitive signal from one video
transcript for a Product Manager. Return valid JSON with exactly these keys, all present:
customer_problems, product_philosophy, strategic_bets, market_framing,
competitive_signals, customer_voices, notable_quotes, product_mentions.

Each key except product_mentions is a list of {statement, quote}. statement is a
normalized one-liner in your words; quote is verbatim supporting text from the transcript.
product_mentions is a list of {name, does}.

Rules:
- customer_problems are OUTCOMES customers struggle with, never feature descriptions.
- product_philosophy includes what they refuse to do, not only what they pursue.
- competitive_signals includes tensions they are answering even when no rival is named:
  defensive pricing language, parity claims, overemphasized differentiation.
- customer_voices is reserved for featured customers speaking — keep it separate from
  company voice.
- notable_quotes is leadership or founder voice only. Not the narrator. Not a customer.
- If a statement cannot be anchored to a verbatim quote, omit it.
- Return only the JSON object. No preamble, no markdown.
```

---

## Pass 2 — per-company canvas

Input: every Pass 1 summary for the company, joined with each video's title + published
date, ordered by date. Output: one canvas object, then a rendered markdown report.

Top-level executive summary + nine sections, fixed order:

```yaml
canvas:
  meta:
    company_slug: "productside"
    run_date: "2026-06-30"
    lookback_window: "30 months"
    video_count: 50
    model: "gpt-4o-mini"
  executive_summary: >
    Productside is positioning itself as the antidote to feature-factory product management,
    betting heavily that the market is ready to reward outcome-driven PMs over delivery-focused
    ones. Their pivot into AI-augmented product workflows in late 2025 is either a genuine
    category move or a hedge against commoditization of their core training content — they
    haven't said which. For a PM leader preparing to compete or partner with them, the
    unspoken question is whether their methodology scales beyond coaching engagements into
    a repeatable product of its own.
  sections:
    product_line:              # Synthesized from product_mentions across ALL videos
      - statement: "Optimal Product Process — structured methodology for outcome-driven product teams"
        signal_strength: 12   # distinct videos mentioning it
        evidence:
          - {video: "...", date: "2025-04-02", quote: "..."}
    problem_obsession:         # The problem they're obsessed with
      - statement: "normalized claim"
        signal_strength: 30
        evidence:
          - {video: "...", date: "2025-04-02", quote: "..."}
    building_for:              # Who they're building for — archetype/mindset/JTBD, not demographics
      - {statement: "...", signal_strength: 0, evidence: []}
    how_they_decide:           # How they decide what to build — revealed product philosophy
      - {statement: "...", signal_strength: 0, evidence: []}
    placing_bets:              # Where they're placing bets — capability, expansion, moves
      - {statement: "...", signal_strength: 0, evidence: []}
    category_framing:          # How they frame the category — defining new space vs competing in one
      - {statement: "...", signal_strength: 0, evidence: []}
    momentum_tone:             # Direction + sentiment — offense/defense, confident/hedging, accel/consolidate
      - {statement: "...", signal_strength: 0, evidence: []}
    whats_shifted:             # What's shifted — stopped saying, newly saying, narrative drift
      - {statement: "...", signal_strength: 0, evidence: []}
    not_saying:                # What they're NOT saying — conspicuous gaps, defensive posture
      - {statement: "...", signal_strength: 0, evidence: []}
```

### Pass 2 synthesis rules

- **`executive_summary` is a top-level string**, not a section with claims. 3-4 sentences.
  Synthesizes who the company is, what they make, and where they appear to be headed.
  Use the company's own language and framing. Written for a PM who needs a 30-second
  context load before reading the sections.
- **`product_line` is synthesized from `product_mentions`.** Statement format:
  "ProductName — what it does in one clause." Signal strength = distinct videos mentioning
  it. Order claims by signal_strength descending so the most-discussed products surface
  first. Evidence = best verbatim quote featuring that product.
- **`signal_strength` is computed here, not extracted.** It is the number of distinct
  videos in which a normalized statement appears. Aggregate aggressively — if 15 videos
  touch the same theme, that is ONE claim with signal_strength 15, not 15 separate claims
  with signal_strength 1. Signal strength is the dial that separates a real pillar from
  a stray aside.
- **`momentum_tone` is explicit tonal analysis.** Assess: (1) offense vs. defense —
  are they expanding and inviting new customers or justifying and preserving? (2) confident
  vs. hedging — certainty of language; (3) accelerating vs. consolidating — are they
  moving into new territory or solidifying existing ground? Each claim is a specific tonal
  signal; evidence quotes should reveal tone, not just subject matter.
- **`building_for` is reconstructed**, not copied. Synthesize the archetype from
  `customer_problems` and `customer_voices`. Describe the mindset and the job, not age/title.
- **`not_saying` requires category reasoning.** Compare what's present against what a
  company in this category would normally cover. Use `competitive_signals` for the
  defensive-posture half. For the gap half, reason explicitly about expected-but-absent
  topics. Name the gap and say why its absence is notable.
- **`whats_shifted` is the temporal section.** It needs the published-date ordering.
  Contrast early-window messaging against late-window messaging.
- Order evidence within each claim by date. Cap at the few strongest quotes per claim;
  `signal_strength` already carries the volume.
- For evidence `quote` values, use VERBATIM text from the `quote` fields in the per-video
  summaries — never a `statement` (normalized analyst summary). If no verbatim quote fits,
  omit that evidence item rather than paraphrasing.

### Pass 2 system prompt

```
You are a strategic advisor preparing a decision-support briefing for a Product Manager
leader — a coach, trainer, or executive who will use this to make decisions about
competing against, partnering with, or building training material around this company.
You have per-video extracted summaries from one company's YouTube channel over a fixed
lookback window, ordered by date.

Your job is INSIGHTS, not data. The difference:
- Data: "They mentioned the Enso Prime lenses in 6 videos."
- Insight: "They are using the Enso Prime lenses to buy entry into a customer segment
  they previously priced out — which is either a TAM expansion bet or a defensive hedge
  against affordable competitors. They don't say which. That ambiguity is itself a signal."

Return a JSON object with exactly two top-level keys:

"executive_summary": A string. 3-4 sentences of STRATEGIC INSIGHT, not company
description. The reader already knows this company exists. Answer: What is this company
trying to do that they haven't fully said out loud? What should a PM leader know before
walking into a room with them, competing against them, or teaching about them? Lead with
the most surprising or consequential thing in the data. Do not open with the company name
or describe what they make — product_line covers that.

"sections": An object with exactly these nine section keys in this order:
product_line, problem_obsession, building_for, how_they_decide, placing_bets,
category_framing, momentum_tone, whats_shifted, not_saying.

Each section is a list of claims. Each claim has:
- statement: A STRATEGIC INSIGHT. Draw a conclusion. Don't hedge. What does this mean
  for a PM leader? "They do X" is data. "They do X because they believe Y, which means
  Z for competitors" is an insight.
- signal_strength: count of DISTINCT videos supporting this statement (integer)
- evidence: list of up to 3 strongest {video, date, quote} anchors

Section guidance:

product_line — EXHAUSTIVE inventory: include EVERY distinct product or product family
mentioned across all videos. Miss nothing — this is the one section where completeness
beats selectivity. Statement format: "ProductName — what it does, and what its presence
in the lineup signals strategically." Signal_strength = distinct videos mentioning it.
Order by signal_strength descending. If no verbatim quote fits, still include the product
claim with empty evidence — do NOT write "No quote" as a placeholder.

problem_obsession — Not just what problem they solve, but WHY this problem — what does
their obsession with it reveal about their beliefs about the market? One aggregated claim
with signal_strength 10 beats 10 thin claims with signal_strength 1.

building_for — Name the mindset and JTBD, then state the implication: who they are NOT
building for, and whether that exclusion is deliberate positioning or a blind spot.

how_they_decide — Surface the principle behind the pattern. "They refuse to do X because
they believe Y" is an insight. What constraint or belief drives their product decisions?

placing_bets — State the bet AND the belief behind it. What must be true for this bet to
pay off? If that assumption turns out wrong, what breaks first?

category_framing — Genuine category creation, or reframing to escape competitive
comparison? What does their framing protect them from having to answer?

momentum_tone — Lead with the verdict: ON OFFENSE or ON DEFENSE, and what proves it.
Then: what does the tone reveal about what they are worried about but won't say?

whats_shifted — What changed between early-window and late-window content? Name what
disappeared and what appeared. State what the DIRECTION of that shift signals about
where they are headed next.

not_saying — Most valuable section. For each gap: name the absence, explain what a
company in this category would normally say, and state the strategic implication —
vulnerability, deliberate positioning, or signal of something unannounced? Thin evidence
is expected; carry the reasoning in the statement.

Aggregation rules:
- Collapse aggressively. Theme across 15 videos = ONE claim with signal_strength 15.
- For evidence quotes, use VERBATIM text from the quote fields only — never a statement.
  Omit an evidence item rather than paraphrase.
- momentum_tone and not_saying claims may have no evidence — the statement carries the
  strategic reasoning.

Return only the JSON. No preamble, no markdown.
```

---

## Output contract

Two artifacts per run:

1. **Human report** — `reports/<slug>-<date>.md`. Executive summary paragraph followed by
   nine sections rendered as readable markdown, each claim followed by its evidence.
   This is the only file the end-user opens. Keep `reports/` human-only.
2. **Machine canvas** — `.workspace/<slug>/canvas-<date>.json`. The full structured canvas
   above, including `executive_summary` as a top-level string and `sections` as a nested
   object. This is what the future compare step reads. Hidden, never opened by hand.

Render the prose FROM the canvas object. Build the object first, persist it, then write
the markdown. Do not generate prose and structure as two independent passes — they will
drift and the report will stop matching its own evidence.

## Comparison model (what this enables next)

Because every canvas has identical `sections` keys and meta, two reads fall out for free:

- **Cross-company grid** — rows are the nine sections, columns are companies. Read each
  company's latest `canvas-<date>.json`, line up `not_saying` against `not_saying`, etc.
- **Time snapshot** — same company, two run dates, diff the canvases to watch the
  narrative move. `whats_shifted` says it in prose; the canvas diff proves it.

The compare step is out of scope for this spec. The contract above is what makes it
cheap to build later. Don't optimize for it now; just don't break it.

## Open TODOs

- **`target_archetype` in Pass 1.** Currently `building_for` is derived in Pass 2. If it
  reads mushy in testing on real channels, add a `target_archetype` list to Pass 1
  ({statement, quote}) and let Pass 2 aggregate it instead of reconstructing. Cheap to add,
  so wait for evidence before adding it.
- **Sentiment tagging.** `momentum_tone` currently captures tonal signals as free-form
  claims. If cross-company comparisons need machine-readable offense/defense scores,
  add a structured `{dimension, value, confidence}` field to each momentum_tone claim.
  Wait for evidence that free-form claims are insufficient.
