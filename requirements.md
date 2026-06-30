# Requirements

## Python packages

```bash
pip install openai openai-whisper
```

## System tools

These must be installed separately before running the agent:

| Tool | What it does | Install |
|---|---|---|
| `yt-dlp` | Downloads video metadata and audio from YouTube | `brew install yt-dlp` |
| `ffmpeg` | Audio processing | `brew install ffmpeg` |

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Used for the AI synthesis step |

Add to your shell profile to make it permanent:

```bash
export OPENAI_API_KEY=your_key_here
```
