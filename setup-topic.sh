#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv-topic"
PYTHON_BIN="python3"

echo "Setting up the optional topical retrieval environment..."

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3 was not found. Run the main setup first: bash setup.sh"
    exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
"$VENV_DIR/bin/python" -m pip install --quiet -r requirements-topic.txt
"$VENV_DIR/bin/python" -m ipykernel install --user \
    --name "yt-channel-intelligence-topic" \
    --display-name "YT Channel Intelligence (topic)"

echo ""
echo "Topical retrieval is ready."
echo ""
echo "Use:"
echo "  .venv-topic/bin/python topic_corpus.py enrich --label-with-llm"
echo "  .venv-topic/bin/python topic_corpus.py index"
echo "  .venv-topic/bin/python topic_corpus.py query \"your question\""
echo "  .venv-topic/bin/python topic_corpus.py export"
echo ""
echo "In Jupyter, select the kernel: YT Channel Intelligence (topic)"
