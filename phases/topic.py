import json
import os
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from config import DATA_DIR


def _yaml_value(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _playlist_id(url: str) -> str:
    return parse_qs(urlparse(url).query).get("list", [""])[0]


def _timestamp_seconds(value: str) -> int:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + int(float(seconds))


def _timestamped_markdown(srt_text: str, source_url: str) -> str:
    sections = []
    for block in re.split(r"\n\s*\n", srt_text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start, end = [part.strip() for part in lines[1].split("-->", 1)]
        text = " ".join(lines[2:])
        seconds = _timestamp_seconds(start)
        separator = "&" if "?" in source_url else "?"
        deep_link = f"{source_url}{separator}t={seconds}s"
        sections.append(
            f"**[{start[:8]}]({deep_link})** {text}"
            f"  \n<!-- end: {end[:12]} -->"
        )
    return "\n\n".join(sections)


def build_corpus(
    workspace_slug: str,
    topic_name: str,
    source_url: str,
    conn,
) -> tuple[str, int]:
    rows = conn.execute(
        """
        SELECT * FROM videos
        WHERE transcript_path IS NOT NULL
          AND status IN ('transcribed', 'analyzed')
        ORDER BY playlist_index, published, title
        """
    ).fetchall()

    records = []
    for row in rows:
        video = dict(row)
        raw_path = video["transcript_path"]
        record_dir = os.path.dirname(raw_path)
        stem = os.path.splitext(os.path.basename(raw_path))[0]
        srt_path = os.path.join(record_dir, f"{stem}.srt")
        canonical_path = os.path.join(record_dir, "transcript.md")

        with open(raw_path, encoding="utf-8") as f:
            raw_text = f.read().strip()

        timestamped_text = ""
        if os.path.exists(srt_path):
            with open(srt_path, encoding="utf-8") as f:
                timestamped_text = _timestamped_markdown(
                    f.read(),
                    video["source_url"],
                )

        metadata = {
            "corpus_type": "topic",
            "corpus_slug": workspace_slug.split("/")[-1],
            "topic": topic_name,
            "taxonomy_version": "workup-0",
            "video_id": video["video_id"],
            "title": video["title"],
            "published": video["published"] or "",
            "duration_seconds": video["duration"] or 0,
            "channel": video["channel"] or "",
            "channel_id": video["channel_id"] or "",
            "playlist_id": video["playlist_id"] or _playlist_id(source_url),
            "playlist_title": video["playlist_title"] or "",
            "playlist_index": video["playlist_index"] or 0,
            "youtube_url": video["source_url"],
            "keywords": [],
            "topic_labels": [],
        }

        frontmatter = ["---"]
        frontmatter += [
            f"{key}: {_yaml_value(value)}"
            for key, value in metadata.items()
        ]
        frontmatter += ["---", "", f"# {video['title']}", "", "## Transcript", ""]
        body = timestamped_text or raw_text

        with open(canonical_path, "w", encoding="utf-8") as f:
            f.write("\n".join(frontmatter))
            f.write(body)
            f.write("\n")

        records.append({
            "video_id": video["video_id"],
            "title": video["title"],
            "playlist_index": video["playlist_index"] or 0,
            "canonical_transcript": canonical_path,
            "raw_transcript": raw_path,
            "subtitles": srt_path if os.path.exists(srt_path) else "",
            "youtube_url": video["source_url"],
        })

    corpus_dir = os.path.join(DATA_DIR, workspace_slug)
    manifest_path = os.path.join(corpus_dir, "corpus.json")
    manifest = {
        "corpus_type": "topic",
        "corpus_slug": workspace_slug.split("/")[-1],
        "topic": topic_name,
        "taxonomy_version": "workup-0",
        "source_url": source_url,
        "playlist_id": _playlist_id(source_url),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "video_count": len(records),
        "records": records,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return manifest_path, len(records)
