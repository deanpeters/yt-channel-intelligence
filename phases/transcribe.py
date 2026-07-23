import os
import subprocess

import db
from config import DATA_DIR, WHISPER_MODEL


def run(
    company_slug: str,
    conn,
    whisper_model: str = WHISPER_MODEL,
    per_video_dirs: bool = False,
    max_playlist_index: int | None = None,
) -> int:
    db.recover_stale_work(conn)
    videos = db.get_transcription_queue(
        conn,
        max_playlist_index=max_playlist_index,
    )
    if not videos:
        print("All videos already transcribed.")
        return 0

    transcripts_dir = os.path.join(DATA_DIR, company_slug, "transcripts")
    os.makedirs(transcripts_dir, exist_ok=True)

    print(f"Transcribing {len(videos)} video(s)...")

    completed = 0
    for video in videos:
        video_id = video["video_id"]
        audio_path = video["audio_path"]
        attempt_id = db.begin_attempt(
            conn,
            video_id,
            "transcription",
            f"transcribe-{os.getpid()}",
        )
        output_dir = (
            os.path.join(transcripts_dir, video_id)
            if per_video_dirs
            else transcripts_dir
        )
        os.makedirs(output_dir, exist_ok=True)

        result = subprocess.run(
            [
                "whisper",
                audio_path,
                "--model", whisper_model,
                "--output-dir", output_dir,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            error = result.stderr.strip()
            db.finish_attempt(
                conn,
                attempt_id,
                video_id,
                "failed",
                error=error,
            )
            print(f"  Deferred {video_id}: {error[:120]}")
            continue

        stem = os.path.splitext(os.path.basename(audio_path))[0]
        transcript_path = os.path.join(output_dir, f"{stem}.txt")

        if not os.path.exists(transcript_path):
            error = "Transcript file not found after transcription"
            db.finish_attempt(
                conn,
                attempt_id,
                video_id,
                "failed",
                error=error,
            )
            print(f"  Deferred {video_id}: {error}")
            continue

        db.finish_attempt(
            conn,
            attempt_id,
            video_id,
            "succeeded",
            status="transcribed",
            transcript_path=transcript_path,
        )
        completed += 1
        print(f"  Transcribed {completed}/{len(videos)}: {video['title'][:60]}")

    print(f"Transcription complete: {completed}/{len(videos)} succeeded.")
    return completed
