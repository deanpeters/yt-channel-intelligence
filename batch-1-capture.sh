#!/usr/bin/env bash
# STEP 1 of 2: capture a playlist batch, then draft case configs for review.
#
#   bash batch-1-capture.sh "<playlist-url>" <up-to-position>
#
# Example (capture through video 50):
#   bash batch-1-capture.sh "https://www.youtube.com/playlist?list=PLZ6..." 50
#
# When this finishes it tells you the ONE file to review, then run
# batch-2-build.sh to finish.
set -euo pipefail

URL="${1:-}"
LIMIT="${2:-}"
TOPIC="${TOPIC:-Business failures}"

if [[ -z "$URL" || -z "$LIMIT" ]]; then
    echo "Usage: bash batch-1-capture.sh \"<playlist-url>\" <up-to-position>"
    exit 1
fi

# Build environments if they are missing.
[[ -x ".venv-capture/bin/python" ]] || bash setup-capture.sh
[[ -x ".venv-topic/bin/python" ]]   || bash setup-topic.sh

SLUG="$(printf '%s' "$TOPIC" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"

echo "==> Capturing \"$TOPIC\" through position $LIMIT (this can take a while)..."
TOPIC="$TOPIC" bash capture-topic.sh "$URL" "$LIMIT"

echo "==> Drafting case configs for the new videos..."
.venv-topic/bin/python topic_corpus.py draft-cases

cat <<EOF

============================================================
STEP 1 DONE.

Now do ONE thing by hand:
  1. Open:  reports/topics/${SLUG}-draft-cases.yaml
  2. Check the case roles and sponsor timestamps.
  3. Copy its entries into the cases: block of:
            topics/${SLUG}.yaml

Then run STEP 2:
  bash batch-2-build.sh
============================================================
EOF
