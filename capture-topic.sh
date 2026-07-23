#!/usr/bin/env bash
# Capture (download + transcribe) a topical playlist batch, resumably.
#
# Usage:
#   bash capture-topic.sh <playlist-url> [limit]
#
# Examples:
#   bash capture-topic.sh "https://www.youtube.com/playlist?list=PLxxxx" 35
#   TOPIC="Business failures" bash capture-topic.sh "$URL" 50
#
# Environment overrides:
#   TOPIC          topic name (default "Business failures")
#   WHISPER_MODEL  whisper model (default small.en)
#   DOWNLOAD_WORKERS  concurrent downloads (default 3)
#
# Safe to re-run: completed videos are skipped, and the queue resumes where it
# left off. This script also does one automatic mop-up pass to retry transient
# download failures (e.g. HTTP 403) within the limit.
set -euo pipefail

URL="${1:-}"
LIMIT="${2:-35}"
TOPIC="${TOPIC:-Business failures}"
WHISPER_MODEL="${WHISPER_MODEL:-small.en}"
DOWNLOAD_WORKERS="${DOWNLOAD_WORKERS:-3}"
VENV_DIR=".venv-capture"

if [[ -z "$URL" ]]; then
    echo "Usage: bash capture-topic.sh <playlist-url> [limit]"
    exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "Capture environment missing; running setup-capture.sh first..."
    bash setup-capture.sh
fi

# Derive the workspace slug the same way agent.py does.
SLUG="$(printf '%s' "$TOPIC" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
DB=".workspace/topics/${SLUG}/channel.db"

run_capture() {
    "$VENV_DIR/bin/python" agent.py \
        --mode topic \
        --topic "$TOPIC" \
        --limit "$LIMIT" \
        --whisper-model "$WHISPER_MODEL" \
        --download-workers "$DOWNLOAD_WORKERS" \
        --download-sleep-min 2 \
        --download-sleep-max 6 \
        "$URL"
}

echo "Capturing \"$TOPIC\" up to playlist position $LIMIT (model: $WHISPER_MODEL)..."
run_capture

# Mop-up: clear retry backoff for any incomplete video within the limit, then
# run once more. This recovers transient download failures without waiting.
if [[ -f "$DB" ]]; then
    STUCK="$("$VENV_DIR/bin/python" - "$DB" "$LIMIT" <<'PY'
import sqlite3, sys
db, limit = sys.argv[1], int(sys.argv[2])
c = sqlite3.connect(db)
rows = c.execute(
    "SELECT COUNT(*) FROM videos "
    "WHERE status IN ('download_failed','downloaded','transcription_failed') "
    "AND (playlist_index = 0 OR playlist_index <= ?)",
    (limit,),
).fetchone()[0]
if rows:
    c.execute(
        "UPDATE videos SET next_retry_at = NULL "
        "WHERE status IN ('download_failed','transcription_failed') "
        "AND (playlist_index = 0 OR playlist_index <= ?)",
        (limit,),
    )
    c.commit()
print(rows)
PY
)"
    if [[ "${STUCK:-0}" -gt 0 ]]; then
        echo "Mop-up pass: retrying $STUCK incomplete video(s)..."
        run_capture
    fi
fi

echo "Capture complete for \"$TOPIC\" (positions <= $LIMIT)."
echo "Next, in the topic environment (.venv-topic):"
echo "  .venv-topic/bin/python topic_corpus.py draft-cases   # draft configs for new videos"
echo "  # review and paste into topics/${SLUG}.yaml, then:"
echo "  .venv-topic/bin/python topic_corpus.py enrich --label-with-llm"
echo "  .venv-topic/bin/python topic_corpus.py index"
