"""Stratified label-review harness for the topical enrichment layer.

Machine-applied passage labels (`review_status: machine_workup`) are unaudited.
This module draws a reproducible stratified sample into a review worksheet, and
converts the reviewer's marked-up worksheet back into `passage_overrides` that
the enrichment step already understands (add/remove labels, correct epistemic
status). Corrections stay in the hand-curated topic config; this only emits a
snippet to paste, never rewrites that file.
"""
import csv
import json
import random
from pathlib import Path

from phases.topic_enrich import load_topic_config

# Machine columns are reference-only; the reviewer fills the columns below.
REVIEW_COLUMNS = [
    "verdict",  # ok | fix | (blank = not reviewed)
    "add_failure_mechanisms",
    "remove_failure_mechanisms",
    "add_causal_roles",
    "remove_causal_roles",
    "set_epistemic_status",
    "note",
]
MACHINE_COLUMNS = [
    "passage_id",
    "subject",
    "playlist_index",
    "start_seconds",
    "deep_link",
    "epistemic_status",
    "failure_mechanisms",
    "causal_roles",
    "actors",
    "evidence_types",
    "summary",
    "text",
]
LIST_OVERRIDE_FIELDS = (
    "failure_mechanisms",
    "causal_roles",
)


def _stratum_key(passage: dict, stratify_by: str) -> str:
    if stratify_by == "case":
        return passage["case"]["subject"]
    if stratify_by == "epistemic":
        return passage["labels"].get("epistemic_status", "(unset)")
    if stratify_by == "mechanism":
        mechanisms = passage["labels"].get("failure_mechanisms", [])
        return mechanisms[0] if mechanisms else "(none)"
    raise ValueError(f"Unknown stratify_by: {stratify_by}")


def load_content_passages(config: dict) -> list[dict]:
    passages_path = Path(config["workspace"]) / "enrichment" / "passages.jsonl"
    passages = [
        json.loads(line)
        for line in passages_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [
        passage
        for passage in passages
        if passage.get("include_in_index") and not passage.get("is_sponsor")
    ]


def stratified_sample(
    passages: list[dict],
    per_stratum: int,
    stratify_by: str = "case",
    seed: int = 0,
) -> list[dict]:
    """Draw up to `per_stratum` passages from each stratum, reproducibly."""
    strata: dict[str, list[dict]] = {}
    for passage in passages:
        strata.setdefault(_stratum_key(passage, stratify_by), []).append(passage)

    rng = random.Random(seed)
    chosen = []
    for key in sorted(strata):
        group = sorted(strata[key], key=lambda p: p["passage_id"])
        if len(group) <= per_stratum:
            chosen.extend(group)
        else:
            chosen.extend(rng.sample(group, per_stratum))
    chosen.sort(
        key=lambda p: (p.get("playlist_index", 0), p["start_seconds"])
    )
    return chosen


def _deep_link(passage: dict) -> str:
    url = passage["youtube_url"]
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}t={passage['start_seconds']}s"


def write_review_worksheet(sample: list[dict], path: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MACHINE_COLUMNS + REVIEW_COLUMNS)
        writer.writeheader()
        for passage in sample:
            labels = passage["labels"]
            row = {
                "passage_id": passage["passage_id"],
                "subject": passage["case"]["subject"],
                "playlist_index": passage.get("playlist_index", 0),
                "start_seconds": passage["start_seconds"],
                "deep_link": _deep_link(passage),
                "epistemic_status": labels.get("epistemic_status", ""),
                "failure_mechanisms": ",".join(labels.get("failure_mechanisms", [])),
                "causal_roles": ",".join(labels.get("causal_roles", [])),
                "actors": ",".join(labels.get("actors", [])),
                "evidence_types": ",".join(labels.get("evidence_types", [])),
                "summary": labels.get("summary", ""),
                "text": passage["text"],
            }
            row.update({column: "" for column in REVIEW_COLUMNS})
            writer.writerow(row)
    return path


def _split(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def review_to_overrides(csv_path: str) -> tuple[dict, dict]:
    """Convert a marked-up worksheet into passage_overrides plus a summary.

    A row is an override when the reviewer typed any correction, or marked the
    verdict `ok`/`fix`. `ok` with no correction records a confirmation (marks
    the passage curated without changing labels)."""
    overrides: dict[str, dict] = {}
    reviewed = confirmed = corrected = 0
    with open(csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            passage_id = (row.get("passage_id") or "").strip()
            verdict = (row.get("verdict") or "").strip().lower()
            entry = {}
            for field in LIST_OVERRIDE_FIELDS:
                for action in ("add", "remove"):
                    values = _split(row.get(f"{action}_{field}", ""))
                    if values:
                        entry[f"{action}_{field}"] = values
            new_status = (row.get("set_epistemic_status") or "").strip()
            if new_status:
                entry["set_epistemic_status"] = new_status
            note = (row.get("note") or "").strip()

            has_correction = bool(entry)
            if not has_correction and verdict not in ("ok", "keep", "fix"):
                continue  # not reviewed
            reviewed += 1
            if has_correction:
                corrected += 1
                if note:
                    entry["note"] = note
            else:
                confirmed += 1
                entry["note"] = note or "reviewed: confirmed"
            overrides[passage_id] = entry

    summary = {
        "reviewed": reviewed,
        "confirmed": confirmed,
        "corrected": corrected,
        "error_rate": round(corrected / reviewed, 3) if reviewed else 0.0,
    }
    return overrides, summary


def _yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(values) + "]"


def overrides_to_yaml_snippet(overrides: dict) -> str:
    """Render overrides as a passage_overrides snippet to paste into the config."""
    lines = ["passage_overrides:"]
    for passage_id in sorted(overrides):
        entry = overrides[passage_id]
        lines.append(f"  {passage_id}:")
        for key, value in entry.items():
            if isinstance(value, list):
                lines.append(f"    {key}: {_yaml_list(value)}")
            else:
                lines.append(f"    {key}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def build_review_worksheet(
    config_path: str,
    per_stratum: int,
    stratify_by: str,
    seed: int,
    output_path: str,
) -> tuple[str, int]:
    config = load_topic_config(config_path)
    passages = load_content_passages(config)
    sample = stratified_sample(passages, per_stratum, stratify_by, seed)
    write_review_worksheet(sample, output_path)
    return output_path, len(sample)


def apply_review_worksheet(csv_path: str, output_path: str) -> tuple[str, dict]:
    overrides, summary = review_to_overrides(csv_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        overrides_to_yaml_snippet(overrides), encoding="utf-8"
    )
    return output_path, summary
