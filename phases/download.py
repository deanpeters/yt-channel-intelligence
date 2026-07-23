import os
import random
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import db
from config import AUDIO_FORMAT, DATA_DIR


def _download_one(
    video: dict,
    audio_dir: str,
    sleep_min: float,
    sleep_max: float,
) -> dict:
    if sleep_max:
        time.sleep(random.uniform(sleep_min, sleep_max))
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
    return {
        "video": video,
        "out_path": out_path,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run(
    company_slug: str,
    conn,
    max_playlist_index: int | None = None,
    workers: int = 1,
    sleep_min: float = 0,
    sleep_max: float = 0,
) -> int:
    if workers < 1:
        raise ValueError("Download workers must be at least 1")
    if sleep_min < 0 or sleep_max < sleep_min:
        raise ValueError("Download sleep range is invalid")
    recovered = db.recover_stale_work(conn)
    if recovered:
        print(f"Recovered {recovered} stale queue claim(s).")
    videos = db.get_download_queue(
        conn,
        max_playlist_index=max_playlist_index,
    )
    if not videos:
        print("All videos already downloaded.")
        return 0

    audio_dir = os.path.join(DATA_DIR, company_slug, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    print(
        f"Downloading audio for {len(videos)} video(s) "
        f"with {workers} worker(s)..."
    )

    completed = 0
    attempts = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for index, video in enumerate(videos):
            worker_id = f"download-{os.getpid()}-{index + 1}"
            attempts[video["video_id"]] = db.begin_attempt(
                conn,
                video["video_id"],
                "download",
                worker_id,
            )
            future = executor.submit(
                _download_one,
                video,
                audio_dir,
                sleep_min,
                sleep_max,
            )
            futures[future] = video

        for future in as_completed(futures):
            result = future.result()
            video = result["video"]
            video_id = video["video_id"]
            attempt_id = attempts[video_id]
            if result["returncode"] != 0:
                error = result["stderr"].strip()
                db.finish_attempt(
                    conn,
                    attempt_id,
                    video_id,
                    "failed",
                    error=error,
                )
                print(f"  Deferred {video_id}: {error[:120]}")
                continue

            raw_date = result["stdout"].strip()
            published = (
                f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
                if len(raw_date) == 8 and raw_date.isdigit()
                else ""
            )
            db.finish_attempt(
                conn,
                attempt_id,
                video_id,
                "succeeded",
                status="downloaded",
                audio_path=result["out_path"],
                published=published,
            )
            completed += 1
            print(
                f"  Downloaded {completed}/{len(videos)}: "
                f"{video['title'][:60]}"
            )

    print(f"Download complete: {completed}/{len(videos)} succeeded.")
    return completed
