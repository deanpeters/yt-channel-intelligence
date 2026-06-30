import json
import subprocess
from datetime import datetime, timedelta

import db
from config import LOOKBACK_MONTHS, MAX_VIDEOS


def run(channel_url: str, conn) -> int:
    cutoff = datetime.now() - timedelta(days=LOOKBACK_MONTHS * 30)
    dateafter = cutoff.strftime("%Y%m%d")

    print(f"Discovering videos since {cutoff.strftime('%B %Y')}...")

    # Fetch 5x MAX_VIDEOS entries to give shorts/showreel filtering enough headroom
    # without pulling the entire channel history.
    result = subprocess.run(
        [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--dateafter", dateafter,
            "--playlist-end", str(MAX_VIDEOS * 5),
            channel_url,
        ],
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
        }
        if _is_short(entry) or _is_showreel(entry):
            low_value.append(item)
        else:
            regular.append(item)

    # Fill MAX_VIDEOS from substantive content first; fall back to low-value only if needed
    selected = regular[:MAX_VIDEOS]
    if len(selected) < MAX_VIDEOS:
        selected += low_value[:MAX_VIDEOS - len(selected)]

    for item in selected:
        db.upsert_video(conn, **item)

    skipped = len(low_value) - max(0, len(selected) - len(regular))
    skip_note = f", {skipped} shorts/showreels skipped" if skipped else ""
    capped = " (capped)" if len(regular) + len(low_value) > MAX_VIDEOS else ""
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
