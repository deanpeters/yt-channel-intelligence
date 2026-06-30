import os
import subprocess

import db
from config import AUDIO_FORMAT, DATA_DIR


def run(company_slug: str, conn) -> int:
    videos = db.get_videos_below_status(conn, "downloaded")
    if not videos:
        print("All videos already downloaded.")
        return 0

    audio_dir = os.path.join(DATA_DIR, company_slug, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    print(f"Downloading audio for {len(videos)} video(s)...")

    completed = 0
    for video in videos:
        video_id = video["video_id"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        out_path = os.path.join(audio_dir, f"{video_id}.{AUDIO_FORMAT}")

        result = subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format", AUDIO_FORMAT,
                "-o", out_path,
                "--no-playlist",
                "--no-simulate",
                "--print", "%(upload_date)s",
                url,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  Skipping {video_id}: {result.stderr.strip()[:120]}")
            continue

        raw_date = result.stdout.strip()
        published = (
            f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            if len(raw_date) == 8 and raw_date.isdigit()
            else ""
        )
        db.set_status(conn, video_id, "downloaded", audio_path=out_path, published=published)
        completed += 1
        print(f"  Downloaded {completed}/{len(videos)}: {video['title'][:60]}")

    print(f"Download complete: {completed}/{len(videos)} succeeded.")
    return completed
