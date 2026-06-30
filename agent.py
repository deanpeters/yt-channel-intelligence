#!/usr/bin/env python3
import argparse
import re
import sys
from urllib.parse import urlparse

import db
from phases import discover, download, transcribe, synthesize


_YT_TAB_SUFFIXES = ("/videos", "/shorts", "/live", "/playlists", "/community", "/about", "/featured")


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    for suffix in _YT_TAB_SUFFIXES:
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    name = path.split("/")[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "channel"


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a YouTube channel and produce a product intelligence report."
    )
    parser.add_argument("url", help="YouTube channel URL")
    args = parser.parse_args()

    company_slug = _slug_from_url(args.url)
    conn = db.get_conn(company_slug)

    try:
        discover.run(args.url, conn)
        download.run(company_slug, conn)
        transcribe.run(company_slug, conn)
        report_path = synthesize.run(company_slug, conn)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print(f"\nReport ready: {report_path}")


if __name__ == "__main__":
    main()
