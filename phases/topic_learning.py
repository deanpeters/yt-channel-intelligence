"""Deterministic learning layer for the topical corpus.

Aggregates the versioned enrichment (`passages.jsonl` + `passage_overrides`)
into source-linked case cards, causal chains, and a cross-case pattern matrix.
No LLM calls: every fact here is a rollup of reviewed labels, and every claim
carries its passage provenance and epistemic status. An LLM prose layer can be
layered on top later, citing these structures.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from phases.topic_enrich import load_topic_config
from phases.topic_review import load_content_passages


def _deep_link(passage: dict) -> str:
    url = passage["youtube_url"]
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}t={passage['start_seconds']}s"


def _passage_ref(passage: dict) -> dict:
    labels = passage["labels"]
    return {
        "passage_id": passage["passage_id"],
        "start_seconds": passage["start_seconds"],
        "deep_link": _deep_link(passage),
        "epistemic_status": labels.get("epistemic_status", ""),
        "summary": labels.get("summary", ""),
        "failure_mechanisms": labels.get("failure_mechanisms", []),
        "causal_roles": labels.get("causal_roles", []),
    }


def _best_passage_for(passages: list[dict], mechanism: str) -> dict | None:
    """Strongest source-linked passage for a mechanism: prefer a direct source
    claim, then the richest (most labels), then earliest in the video."""
    candidates = [
        passage
        for passage in passages
        if mechanism in passage["labels"].get("failure_mechanisms", [])
    ]
    if not candidates:
        return None

    def rank(passage: dict) -> tuple:
        labels = passage["labels"]
        direct = labels.get("epistemic_status") == "direct_source_claim"
        richness = len(labels.get("failure_mechanisms", [])) + len(
            labels.get("causal_roles", [])
        )
        return (direct, richness, -passage["start_seconds"])

    return max(candidates, key=rank)


def build_case_card(
    video_id: str,
    case: dict,
    passages: list[dict],
    causal_role_order: list[str],
) -> dict:
    mechanism_counts = Counter()
    epistemic_counts = Counter()
    evidence_counts = Counter()
    by_role = defaultdict(list)
    for passage in passages:
        labels = passage["labels"]
        for mechanism in labels.get("failure_mechanisms", []):
            mechanism_counts[mechanism] += 1
        epistemic_counts[labels.get("epistemic_status", "")] += 1
        for evidence in labels.get("evidence_types", []):
            evidence_counts[evidence] += 1
        for role in labels.get("causal_roles", []):
            by_role[role].append(passage)

    # Causal chain in taxonomy order; each node keeps its source passages.
    causal_chain = []
    for role in causal_role_order:
        node_passages = by_role.get(role, [])
        if node_passages:
            causal_chain.append({
                "causal_role": role,
                "passages": [_passage_ref(p) for p in node_passages],
            })

    # Evidence gaps: case-level mechanisms never backed by a direct source
    # claim in any passage. These are teaching-worthy "asserted but not shown".
    directly_evidenced = {
        mechanism
        for passage in passages
        if passage["labels"].get("epistemic_status") == "direct_source_claim"
        for mechanism in passage["labels"].get("failure_mechanisms", [])
    }
    evidence_gaps = [
        mechanism
        for mechanism in case.get("failure_mechanisms", [])
        if mechanism not in directly_evidenced
    ]

    key_passages = {}
    for mechanism in case.get("failure_mechanisms", []):
        best = _best_passage_for(passages, mechanism)
        if best:
            key_passages[mechanism] = _passage_ref(best)

    return {
        "video_id": video_id,
        "subject": case["subject"],
        "case_role": case.get("case_role", "unspecified"),
        "subject_type": case.get("subject_type", ""),
        "industry": case.get("industry", ""),
        "geography": case.get("geography", ""),
        "time_period": case.get("time_period", ""),
        "failure_states": case.get("failure_states", []),
        "case_mechanisms": case.get("failure_mechanisms", []),
        "passage_mechanism_counts": dict(mechanism_counts.most_common()),
        "epistemic_breakdown": dict(epistemic_counts),
        "evidence_breakdown": dict(evidence_counts.most_common()),
        "causal_chain": causal_chain,
        "evidence_gaps": evidence_gaps,
        "key_passages": key_passages,
        "passage_count": len(passages),
    }


def build_case_cards(config: dict) -> list[dict]:
    passages = load_content_passages(config)
    by_video = defaultdict(list)
    for passage in passages:
        by_video[passage["video_id"]].append(passage)
    for group in by_video.values():
        group.sort(key=lambda p: p["start_seconds"])

    causal_role_order = config["taxonomy"]["causal_roles"]
    cards = []
    for video_id, case in config["cases"].items():
        cards.append(
            build_case_card(
                video_id,
                case,
                by_video.get(video_id, []),
                causal_role_order,
            )
        )
    cards.sort(key=lambda card: card["subject"].lower())
    return cards


def build_pattern_matrix(cards: list[dict], mechanisms: list[str]) -> list[dict]:
    """One row per case; a cell is the passage count for that mechanism.

    Uses passage-level mechanism counts so the matrix reflects what the
    transcripts actually evidence, not only case-level assertions."""
    rows = []
    for card in cards:
        counts = card["passage_mechanism_counts"]
        row = {"subject": card["subject"], "case_role": card["case_role"]}
        for mechanism in mechanisms:
            row[mechanism] = counts.get(mechanism, 0)
        rows.append(row)
    return rows


def _epistemic_line(breakdown: dict) -> str:
    order = [
        "direct_source_claim",
        "derived_inference",
        "contested_or_unverified",
        "missing_evidence",
    ]
    parts = [f"{key} {breakdown[key]}" for key in order if breakdown.get(key)]
    return ", ".join(parts) or "none"


def render_case_card_md(card: dict) -> str:
    lines = [
        f"# {card['subject']}",
        "",
        f"- **Case role:** {card['case_role']}",
        f"- **Type / industry:** {card['subject_type']} / {card['industry']}",
        f"- **Geography / period:** {card['geography']} / {card['time_period']}",
        f"- **Failure states:** {', '.join(card['failure_states']) or 'none'}",
        f"- **Passages analyzed:** {card['passage_count']}",
        f"- **Evidence mix:** {_epistemic_line(card['epistemic_breakdown'])}",
        "",
        "## Failure mechanisms (case-level, with strongest source passage)",
        "",
    ]
    if card["case_mechanisms"]:
        for mechanism in card["case_mechanisms"]:
            ref = card["key_passages"].get(mechanism)
            count = card["passage_mechanism_counts"].get(mechanism, 0)
            if ref:
                lines.append(
                    f"- **{mechanism}** ({count} passage(s), "
                    f"{ref['epistemic_status']}) — "
                    f"[{ref['start_seconds']}s]({ref['deep_link']}): "
                    f"{ref['summary']}"
                )
            else:
                lines.append(
                    f"- **{mechanism}** — no passage carries this label "
                    "(asserted at case level only)"
                )
    else:
        lines.append("- none recorded")

    lines += ["", "## Causal chain", ""]
    if card["causal_chain"]:
        for node in card["causal_chain"]:
            refs = node["passages"]
            links = ", ".join(
                f"[{ref['start_seconds']}s]({ref['deep_link']})" for ref in refs
            )
            lines.append(f"- **{node['causal_role']}** — {links}")
    else:
        lines.append("- no causal roles labeled")

    lines += ["", "## Evidence gaps", ""]
    if card["evidence_gaps"]:
        lines.append(
            "Mechanisms asserted for this case but never backed by a direct "
            "source claim in a passage (candidates for review or inference "
            "labeling):"
        )
        lines.append("")
        for mechanism in card["evidence_gaps"]:
            lines.append(f"- {mechanism}")
    else:
        lines.append("Every case-level mechanism has at least one direct "
                     "source-claim passage.")
    lines.append("")
    return "\n".join(lines)


def build_learning_layer(config_path: str) -> tuple[str, dict]:
    config = load_topic_config(config_path)
    workspace = Path(config["workspace"])
    learning_dir = workspace / "learning"
    cards_dir = learning_dir / "case-cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    cards = build_case_cards(config)
    for card in cards:
        (cards_dir / f"{card['video_id']}.md").write_text(
            render_case_card_md(card), encoding="utf-8"
        )

    # Machine-readable cards for the LLM prose layer and the notebook.
    (learning_dir / "case-cards.json").write_text(
        json.dumps(cards, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    mechanisms = config["taxonomy"]["failure_mechanisms"]
    matrix = build_pattern_matrix(cards, mechanisms)
    matrix_path = learning_dir / "pattern-matrix.csv"
    with matrix_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["subject", "case_role"] + mechanisms
        )
        writer.writeheader()
        writer.writerows(matrix)

    stats = {
        "cards": len(cards),
        "cases_with_evidence_gaps": sum(
            1 for card in cards if card["evidence_gaps"]
        ),
        "learning_dir": str(learning_dir),
    }
    return str(learning_dir), stats
