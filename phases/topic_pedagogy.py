"""Pedagogic evaluation of the learning layer (Phase 3, item 5).

These are mechanical structural checks over the deterministic case cards and the
LLM teaching notes — evidence about whether the learning artifacts hold up, not
a target to tune the prose against. The checks verify citation integrity,
counterexample coverage, boundary conditions, honest disclosure of evidence
gaps, and within-corpus pattern recurrence (single-case patterns are flagged as
provisional, per the one-channel principle).
"""
import json
from collections import Counter
from pathlib import Path

from phases.topic_enrich import load_topic_config
from phases.topic_teaching import (
    _COUNTEREXAMPLE_ROLES,
    valid_timestamps,
    validate_citations,
)


def run_pedagogy_checks(
    cards: list[dict],
    notes_by_id: dict[str, dict],
    provisional_threshold: int = 1,
) -> dict:
    citation_failures = []
    counterexample_failures = []
    boundary_failures = []
    evidence_gap_failures = []
    recurrence = Counter()

    for card in cards:
        video_id = card["video_id"]
        notes = notes_by_id.get(video_id, {})
        stamps = valid_timestamps(card)

        uncited = validate_citations(notes, stamps)
        if uncited:
            citation_failures.append((card["subject"], uncited))

        lessons = notes.get("lessons", [])
        if lessons and not notes.get("boundary_conditions"):
            boundary_failures.append(card["subject"])

        if card["case_role"] in _COUNTEREXAMPLE_ROLES and not notes.get(
            "counterexample_notes"
        ):
            counterexample_failures.append(card["subject"])

        if card["evidence_gaps"] and not notes.get("cannot_yet_claim"):
            evidence_gap_failures.append(card["subject"])

        for mechanism, count in card["passage_mechanism_counts"].items():
            if count > 0:
                recurrence[mechanism] += 1

    provisional = sorted(
        mechanism
        for mechanism, cases in recurrence.items()
        if cases <= provisional_threshold
    )

    checks = {
        "citation_integrity": {
            "pass": not citation_failures,
            "failures": citation_failures,
        },
        "counterexample_coverage": {
            "pass": not counterexample_failures,
            "failures": counterexample_failures,
        },
        "boundary_conditions": {
            "pass": not boundary_failures,
            "failures": boundary_failures,
        },
        "evidence_gap_disclosure": {
            "pass": not evidence_gap_failures,
            "failures": evidence_gap_failures,
        },
        "pattern_recurrence": {
            "by_case_spread": dict(recurrence.most_common()),
            "provisional_single_case": provisional,
        },
    }
    checks["overall_pass"] = all(
        checks[name]["pass"]
        for name in (
            "citation_integrity",
            "counterexample_coverage",
            "boundary_conditions",
            "evidence_gap_disclosure",
        )
    )
    return checks


def _render_report(checks: dict) -> str:
    def status(name):
        return "PASS" if checks[name]["pass"] else "FAIL"

    lines = [
        "# Business Failures Pedagogic Evaluation",
        "",
        "Mechanical checks over the learning layer. These are evidence about "
        "the artifacts, not targets to tune the prose against.",
        "",
        f"**Overall:** {'PASS' if checks['overall_pass'] else 'FAIL'}",
        "",
        "## Gating checks",
        "",
        f"- Citation integrity: {status('citation_integrity')}",
        f"- Counterexample coverage: {status('counterexample_coverage')}",
        f"- Boundary conditions: {status('boundary_conditions')}",
        f"- Evidence-gap disclosure: {status('evidence_gap_disclosure')}",
        "",
    ]
    for name, label in (
        ("citation_integrity", "Lessons citing a timestamp absent from the card"),
        ("counterexample_coverage", "Counterexample cases missing counterexample notes"),
        ("boundary_conditions", "Cases with lessons but no boundary conditions"),
        ("evidence_gap_disclosure", "Cases with evidence gaps not disclosed"),
    ):
        failures = checks[name]["failures"]
        if failures:
            lines.append(f"**{label}:**")
            lines += [f"- {failure}" for failure in failures]
            lines.append("")

    pattern = checks["pattern_recurrence"]
    lines += [
        "## Pattern recurrence (within corpus)",
        "",
        "Number of cases each mechanism appears in. All cases share one "
        "channel, so these are within-corpus patterns, provisional until "
        "corroborated elsewhere.",
        "",
        "| Mechanism | Cases |",
        "|---|---:|",
    ]
    lines += [
        f"| {mechanism} | {cases} |"
        for mechanism, cases in pattern["by_case_spread"].items()
    ]
    lines += [
        "",
        "**Single-case (provisional) mechanisms:** "
        + (", ".join(pattern["provisional_single_case"]) or "none"),
        "",
    ]
    return "\n".join(lines)


def evaluate_pedagogy(config_path: str, output_path: str) -> tuple[str, dict]:
    config = load_topic_config(config_path)
    workspace = Path(config["workspace"])
    learning_dir = workspace / "learning"
    cards_path = learning_dir / "case-cards.json"
    notes_dir = learning_dir / "teaching-notes"
    if not cards_path.exists():
        raise RuntimeError("No case cards found. Run: topic_corpus.py learn")
    if not notes_dir.exists():
        raise RuntimeError("No teaching notes found. Run: topic_corpus.py teach")

    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    notes_by_id = {}
    for card in cards:
        note_path = notes_dir / f"{card['video_id']}.json"
        if note_path.exists():
            notes_by_id[card["video_id"]] = json.loads(
                note_path.read_text(encoding="utf-8")
            )

    checks = run_pedagogy_checks(cards, notes_by_id)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(_render_report(checks), encoding="utf-8")

    summary = {
        "overall_pass": checks["overall_pass"],
        "citation_integrity": checks["citation_integrity"]["pass"],
        "counterexample_coverage": checks["counterexample_coverage"]["pass"],
        "boundary_conditions": checks["boundary_conditions"]["pass"],
        "evidence_gap_disclosure": checks["evidence_gap_disclosure"]["pass"],
        "provisional_single_case": len(
            checks["pattern_recurrence"]["provisional_single_case"]
        ),
    }
    return output_path, summary
