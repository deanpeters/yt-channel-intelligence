#!/usr/bin/env bash
# STEP 2 of 2: after you pasted the reviewed cases into the topic config,
# this labels, indexes, rebuilds the learning + teaching layers, and checks
# that nothing regressed.
#
#   bash batch-2-build.sh
set -euo pipefail

TOPIC="${TOPIC:-Business failures}"
SLUG="$(printf '%s' "$TOPIC" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
PY=".venv-topic/bin/python"

echo "==> Labeling new passages..."
"$PY" topic_corpus.py enrich --label-with-llm >/dev/null

echo "==> Building search index..."
"$PY" topic_corpus.py index

echo "==> Rebuilding case cards and teaching notes..."
"$PY" topic_corpus.py learn >/dev/null
"$PY" topic_corpus.py teach >/dev/null

echo ""
echo "==> Checking nothing regressed:"
echo -n "    fixed regression:  "
"$PY" topic_corpus.py evaluate \
  --output "reports/topics/${SLUG}-retrieval-evaluation.md" >/dev/null \
  && grep -m1 "Strict score" "reports/topics/${SLUG}-retrieval-evaluation.md"

echo -n "    calibration:       "
"$PY" topic_corpus.py evaluate \
  --questions "evaluations/${SLUG}-calibration-questions.yaml" \
  --output "reports/topics/${SLUG}-calibration-evaluation.md" >/dev/null \
  && grep -m1 "Strict score" "reports/topics/${SLUG}-calibration-evaluation.md"

echo -n "    learning quality:  "
"$PY" topic_corpus.py evaluate-learning 2>/dev/null | grep -m1 overall_pass

cat <<EOF

============================================================
DONE. The corpus is updated. Try it:
  .venv-topic/bin/python topic_corpus.py answer "your question here"
============================================================
EOF
