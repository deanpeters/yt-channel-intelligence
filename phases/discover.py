import json
import subprocess
from datetime import datetime, timedelta

import db
from config import LOOKBACK_MONTHS, MAX_VIDEOS


def run(
    channel_url: str,
    conn,
    max_videos: int = MAX_VIDEOS,
    lookback_months: int | None = LOOKBACK_MONTHS,
    materialize_all: bool = False,
) -> int:
    if lookback_months is None:
        print(f"Discovering the first {max_videos} substantive playlist video(s)...")
    else:
        cutoff = datetime.now() - timedelta(days=lookback_months * 30)
        print(f"Discovering videos since {cutoff.strftime('%B %Y')}...")

    # Fetch 5x MAX_VIDEOS entries to give shorts/showreel filtering enough headroom
    # without pulling the entire channel history.
    command = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
    ]
    if not materialize_all:
        command += ["--playlist-end", str(max_videos * 5)]
    if lookback_months is not None:
        command += ["--dateafter", cutoff.strftime("%Y%m%d")]
    command.append(channel_url)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")

    regular = []
    low_value = []  # shorts and showreels — fallback only

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        video_id = entry.get("id")
        if not video_id:
            continue

        item = {
            "video_id":  video_id,
            "title":     entry.get("title", ""),
            "published": entry.get("upload_date", ""),
            "duration":  entry.get("duration") or 0,
            "source_url": entry.get("webpage_url") or entry.get("url") or (
                f"https://www.youtube.com/watch?v={video_id}"
            ),
            "channel": entry.get("channel") or entry.get("uploader") or "",
            "channel_id": entry.get("channel_id") or "",
            "playlist_id": entry.get("playlist_id") or "",
            "playlist_title": entry.get("playlist_title") or entry.get("playlist") or "",
            "playlist_index": entry.get("playlist_index") or 0,
        }
        if _is_short(entry) or _is_showreel(entry):
            low_value.append(item)
        else:
            regular.append(item)

    # Fill the requested limit from substantive content first; fall back to low-value only if needed
    if materialize_all:
        selected = regular + low_value
    else:
        selected = regular[:max_videos]
        if len(selected) < max_videos:
            selected += low_value[:max_videos - len(selected)]

    for item in selected:
        db.upsert_video(conn, **item)

    skipped = len(low_value) - max(0, len(selected) - len(regular))
    skip_note = f", {skipped} shorts/showreels skipped" if skipped else ""
    capped = (
        " (capped)"
        if not materialize_all
        and len(regular) + len(low_value) > max_videos
        else ""
    )
    if materialize_all:
        print(
            f"Queued {len(selected)} videos; "
            f"capture boundary is playlist position {max_videos}."
        )
    else:
        print(f"Found {len(selected)} videos{capped}{skip_note}.")
    return len(selected)


def _is_short(entry: dict) -> bool:
    url = entry.get("url", "") or ""
    if "/shorts/" in url:
        return True
    duration = entry.get("duration") or 0
    return 0 < duration <= 60


def _is_showreel(entry: dict) -> bool:
    title = entry.get("title", "") or ""
    return "showreel" in title.lower()
