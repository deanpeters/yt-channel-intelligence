"""Portable study-archive packaging (Phase 6).

Bundles the durable, shareable layers of a topical corpus into a single
data-only archive: the manifest, canonical transcripts, versioned taxonomy,
enrichment, exports, learning artifacts, evaluations, and the exploration
notebook. Audio and the rebuildable Chroma index are excluded, and nothing in
the archive needs an API key to open — it is meant for pandas, Polars, DuckDB,
Jupyter, Colab, or Antigravity.
"""
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from phases.topic_enrich import load_topic_config
from phases.topic_export import export_corpus

# Anything matching these is never packaged (raw media, rebuildable index).
EXCLUDE_PARTS = ("audio", "chroma_db", ".m4a", ".mp3", ".wav")

ARCHIVE_README = """\
# {topic} — portable study corpus

Data-only export of a topical intelligence corpus. **No API keys are needed to
use anything in here.** Audio and the search index are intentionally excluded;
the search index rebuilds from `enrichment/passages.jsonl`.

## Contents

- `corpus.json` — manifest of every source video (id, title, url, dates).
- `taxonomy.yaml` — the versioned taxonomy and per-case labels.
- `transcripts/` — canonical, timestamped Markdown transcript per video.
- `enrichment/passages.jsonl` — every labeled passage with provenance.
- `exports/` — `cases.csv`, `passages.csv`, `passages.jsonl`,
  `passages.parquet`, and manifests for analysis tools.
- `learning/` — source-linked case cards, causal chains, pattern matrix,
  and teaching notes.
- `evaluations/` — retrieval question sets used to check the corpus.
- `notebook/` — the exploration notebook.

## Quick start

```python
import pandas as pd
passages = pd.read_parquet("exports/passages.parquet")
passages.groupby("subject")["failure_mechanisms"].count()
```

```python
import duckdb
duckdb.sql("SELECT subject, COUNT(*) FROM 'exports/passages.parquet' GROUP BY 1")
```

Every passage keeps its video id, title, URL, and timestamps, so findings stay
traceable to the source.
"""


def plan_archive_contents(
    config_path: str,
    config: dict,
    manifest: dict,
) -> list[tuple[Path, str]]:
    """Return (source_path, archive_name) pairs. Pure: no IO beyond globbing."""
    workspace = Path(config["workspace"])
    items: list[tuple[Path, str]] = []

    def add(src: Path, arcname: str):
        if src.exists() and not any(part in str(src) for part in EXCLUDE_PARTS):
            items.append((src, arcname))

    add(workspace / "corpus.json", "corpus.json")
    add(Path(config_path), "taxonomy.yaml")
    add(workspace / "enrichment" / "passages.jsonl", "enrichment/passages.jsonl")
    add(workspace / "enrichment" / "stats.json", "enrichment/stats.json")

    for record in manifest["records"]:
        transcript = Path(record["canonical_transcript"])
        add(transcript, f"transcripts/{record['video_id']}.md")

    for sub in ("exports", "learning"):
        base = workspace / sub
        if base.exists():
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    add(path, f"{sub}/{path.relative_to(base)}")

    for evaluation in sorted(Path("evaluations").glob("*.yaml")):
        add(evaluation, f"evaluations/{evaluation.name}")

    notebook_dir = Path("notebooks")
    if notebook_dir.exists():
        for notebook in sorted(notebook_dir.glob("*.ipynb")):
            add(notebook, f"notebook/{notebook.name}")

    return items


def build_archive(config_path: str, output_dir: str = "dist") -> tuple[str, dict]:
    config = load_topic_config(config_path)
    workspace = Path(config["workspace"])

    # Ensure exports are current before packaging them.
    export_corpus(config_path)

    manifest = json.loads((workspace / "corpus.json").read_text(encoding="utf-8"))
    items = plan_archive_contents(config_path, config, manifest)

    readme = ARCHIVE_README.format(topic=config.get("topic", config["corpus_slug"]))
    version = config.get("taxonomy_version", "workup").replace(".", "-")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    archive_path = Path(output_dir) / f"{config['corpus_slug']}-{version}.zip"

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", readme)
        zf.writestr(
            "PACKAGE.json",
            json.dumps(
                {
                    "corpus_slug": config["corpus_slug"],
                    "taxonomy_version": config.get("taxonomy_version"),
                    "packaged_at": datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    ),
                    "video_count": len(manifest["records"]),
                    "file_count": len(items),
                },
                indent=2,
            ),
        )
        for src, arcname in items:
            zf.write(src, arcname)

    stats = {
        "archive": str(archive_path),
        "videos": len(manifest["records"]),
        "files": len(items) + 2,  # + README + PACKAGE.json
        "size_bytes": archive_path.stat().st_size,
    }
    return str(archive_path), stats
