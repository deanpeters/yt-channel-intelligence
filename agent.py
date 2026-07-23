#!/usr/bin/env python3
import argparse
import re
import sys
from urllib.parse import urlparse, parse_qs

import db
from config import LOOKBACK_MONTHS, MAX_VIDEOS
from phases import discover, download, synthesize, topic, transcribe


_YT_TAB_SUFFIXES = ("/videos", "/shorts", "/live", "/playlists", "/courses", "/community", "/about", "/featured")


def _slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    # Playlist URLs: use the playlist ID so each playlist gets a unique slug
    qs = parse_qs(parsed.query)
    if "list" in qs:
        playlist_id = qs["list"][0]
        return re.sub(r"[^a-z0-9]+", "-", playlist_id.lower()).strip("-") or "playlist"
    path = parsed.path.rstrip("/")
    for suffix in _YT_TAB_SUFFIXES:
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    name = path.split("/")[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "channel"


def _slug_from_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "topic"


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a company channel or capture a playlist as a topical corpus."
        )
    )
    parser.add_argument("url", help="YouTube channel or playlist URL")
    parser.add_argument(
        "--mode",
        choices=("company", "topic"),
        default="company",
        help="Analysis mode. Existing behavior remains company mode.",
    )
    parser.add_argument(
        "--topic",
        help="Human-readable topic name for topic mode, such as 'Business failures'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum videos to capture. Topic spikes default to 3.",
    )
    parser.add_argument(
        "--whisper-model",
        help="Optional transcription model override, such as small.en.",
    )
    parser.add_argument(
        "--download-workers",
        type=int,
        default=2,
        help="Concurrent topic downloads. Company mode remains single-worker.",
    )
    parser.add_argument(
        "--download-sleep-min",
        type=float,
        default=3,
        help="Minimum randomized delay before each topic download.",
    )
    parser.add_argument(
        "--download-sleep-max",
        type=float,
        default=8,
        help="Maximum randomized delay before each topic download.",
    )
    args = parser.parse_args()

    if args.mode == "topic" and not args.topic:
        parser.error("--topic is required when --mode topic is selected")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.download_workers < 1:
        parser.error("--download-workers must be at least 1")
    if (
        args.download_sleep_min < 0
        or args.download_sleep_max < args.download_sleep_min
    ):
        parser.error("download sleep range is invalid")

    is_topic = args.mode == "topic"
    workspace_slug = (
        f"topics/{_slug_from_name(args.topic)}"
        if is_topic
        else _slug_from_url(args.url)
    )
    conn = db.get_conn(workspace_slug)

    result_path = ""
    try:
        discover.run(
            args.url,
            conn,
            max_videos=args.limit or (3 if is_topic else MAX_VIDEOS),
            lookback_months=None if is_topic else LOOKBACK_MONTHS,
            materialize_all=is_topic,
        )
        capture_limit = args.limit or (3 if is_topic else None)
        download.run(
            workspace_slug,
            conn,
            max_playlist_index=capture_limit if is_topic else None,
            workers=args.download_workers if is_topic else 1,
            sleep_min=args.download_sleep_min if is_topic else 0,
            sleep_max=args.download_sleep_max if is_topic else 0,
        )
        transcribe_kwargs = {
            "per_video_dirs": is_topic,
            "max_playlist_index": capture_limit if is_topic else None,
        }
        if args.whisper_model:
            transcribe_kwargs["whisper_model"] = args.whisper_model
        transcribe.run(workspace_slug, conn, **transcribe_kwargs)
        if is_topic:
            result_path, video_count = topic.build_corpus(
                workspace_slug,
                args.topic,
                args.url,
                conn,
            )
            if video_count == 0:
                raise RuntimeError("No transcripts were available for the topic corpus.")
        else:
            result_path = synthesize.run(workspace_slug, conn)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    label = "Topic corpus" if is_topic else "Report"
    print(f"\n{label} ready: {result_path}")


if __name__ == "__main__":
    main()
