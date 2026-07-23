#!/usr/bin/env bash
# One-time setup for the topical capture environment (.venv-capture).
# Installs yt-dlp and Whisper so you can capture and transcribe videos.
# ffmpeg must be installed separately (e.g. `brew install ffmpeg`).
set -euo pipefail

VENV_DIR=".venv-capture"
PYTHON_BIN="python3"

echo "Setting up the topical capture environment..."

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3 was not found. Install Python 3 first."
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Warning: ffmpeg was not found. Install it before capturing:"
    echo "  macOS:  brew install ffmpeg"
    echo "  Ubuntu: sudo apt-get install ffmpeg"
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
"$VENV_DIR/bin/python" -m pip install --quiet -r requirements-capture.txt

echo "Capture environment ready in $VENV_DIR."
echo "Next: bash capture-topic.sh <playlist-url> [limit]"
