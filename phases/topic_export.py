import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from phases.topic_enrich import load_topic_config


def _joined(values) -> str:
    return "|".join(values or [])


def _passage_row(passage: dict) -> dict:
    labels = passage["labels"]
    case = passage["case"]
    return {
        "passage_id": passage["passage_id"],
        "video_id": passage["video_id"],
        "title": passage["title"],
        "subject": str(case["subject"]),
        "case_role": str(case.get("case_role", "unspecified")),
        "subject_type": str(case["subject_type"]),
        "industry": str(case["industry"]),
        "geography": str(case["geography"]),
        # Coerce to str: a single-year time_period can arrive as an int and
        # would otherwise break the Parquet column's type.
        "time_period": str(case["time_period"]),
        "start_seconds": passage["start_seconds"],
        "end_seconds": passage["end_seconds"],
        "text": passage["text"],
        "summary": labels["summary"],
        "causal_roles": _joined(labels["causal_roles"]),
        "failure_mechanisms": _joined(labels["failure_mechanisms"]),
        "case_failure_mechanisms": _joined(
            case["failure_mechanisms"]
        ),
        "failure_states": _joined(case["failure_states"]),
        "actors": _joined(labels["actors"]),
        "evidence_types": _joined(labels["evidence_types"]),
        "epistemic_status": labels["epistemic_status"],
        "review_status": labels["review_status"],
        "is_sponsor": passage["is_sponsor"],
        "include_in_index": passage["include_in_index"],
        "sponsor_name": passage["sponsor_name"],
        "taxonomy_version": passage["taxonomy_version"],
        "transcript_source": passage["transcript_source"],
        "youtube_url": passage["youtube_url"],
        "deep_link": (
            f"{passage['youtube_url']}"
            f"{'&' if '?' in passage['youtube_url'] else '?'}"
            f"t={passage['start_seconds']}s"
        ),
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"No rows available for {path.name}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_corpus(config_path: str) -> tuple[str, dict]:
    config = load_topic_config(config_path)
    workspace = Path(config["workspace"])
    source_passages = workspace / "enrichment" / "passages.jsonl"
    if not source_passages.exists():
        raise RuntimeError("Run topic enrichment before exporting.")
    passages = [
        json.loads(line)
        for line in source_passages.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    passage_rows = [_passage_row(passage) for passage in passages]
    case_rows = []
    mechanism_rows = []
    for video_id, case in config["cases"].items():
        case_rows.append({
            "video_id": video_id,
            "subject": case["subject"],
            "case_role": case.get("case_role", "unspecified"),
            "subject_type": case["subject_type"],
            "industry": case["industry"],
            "geography": case["geography"],
            "time_period": case["time_period"],
            "failure_states": _joined(case["failure_states"]),
            "failure_mechanisms": _joined(
                case["failure_mechanisms"]
            ),
        })
        for mechanism in case["failure_mechanisms"]:
            mechanism_rows.append({
                "video_id": video_id,
                "subject": case["subject"],
                "failure_mechanism": mechanism,
                "taxonomy_version": config["taxonomy_version"],
            })

    export_dir = workspace / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(export_dir / "cases.csv", case_rows)
    _write_csv(export_dir / "passages.csv", passage_rows)
    _write_csv(
        export_dir / "case_mechanisms.csv",
        mechanism_rows,
    )
    shutil.copyfile(
        source_passages,
        export_dir / "passages.jsonl",
    )

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "Parquet export needs pyarrow. Run: bash setup-topic.sh"
        ) from exc
    pq.write_table(
        pa.Table.from_pylist(passage_rows),
        export_dir / "passages.parquet",
        compression="zstd",
    )

    stats = {
        "exported_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ),
        "taxonomy_version": config["taxonomy_version"],
        "case_count": len(case_rows),
        "passage_count": len(passage_rows),
        "indexed_passage_count": sum(
            bool(row["include_in_index"]) for row in passage_rows
        ),
        "files": [
            "cases.csv",
            "case_mechanisms.csv",
            "passages.csv",
            "passages.jsonl",
            "passages.parquet",
        ],
    }
    (export_dir / "export-manifest.json").write_text(
        json.dumps(stats, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(export_dir), stats
