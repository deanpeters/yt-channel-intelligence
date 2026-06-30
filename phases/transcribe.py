import os
import subprocess

import db
from config import DATA_DIR, WHISPER_MODEL


def run(company_slug: str, conn) -> int:
    videos = db.get_videos_below_status(conn, "transcribed")
    if not videos:
        print("All videos already transcribed.")
        return 0

    transcripts_dir = os.path.join(DATA_DIR, company_slug, "transcripts")
    os.makedirs(transcripts_dir, exist_ok=True)

    print(f"Transcribing {len(videos)} video(s)...")

    completed = 0
    for video in videos:
        if video["status"] != "downloaded":
            continue

        video_id = video["video_id"]
        audio_path = video["audio_path"]

        result = subprocess.run(
            [
                "whisper",
                audio_path,
                "--model", WHISPER_MODEL,
                "--output-dir", transcripts_dir,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  Skipping {video_id}: {result.stderr.strip()[:120]}")
            continue

        stem = os.path.splitext(os.path.basename(audio_path))[0]
        transcript_path = os.path.join(transcripts_dir, f"{stem}.txt")

        if not os.path.exists(transcript_path):
            print(f"  Skipping {video_id}: transcript file not found after transcription")
            continue

        db.set_status(conn, video_id, "transcribed", transcript_path=transcript_path)
        completed += 1
        print(f"  Transcribed {completed}/{len(videos)}: {video['title'][:60]}")

    print(f"Transcription complete: {completed}/{len(videos)} succeeded.")
    return completed
