# CLAUDE.md — Channel Intelligence Agent

## What this project does

Takes a YouTube channel URL and produces a structured competitive intelligence report aimed at product managers preparing for meetings. One command in, one report out.

## Primary user

Product managers preparing for meetings, building competitive intelligence, or creating training material. Not engineers, not data scientists. Design everything accordingly.

## Design principles

- `reports/` is the only directory the user ever opens
- All pipeline scratch data (audio, transcripts, SQLite) lives in `.workspace/` — hidden by default in Finder and Explorer
- When the tool finishes, print exactly one line telling the user where their report is
- CLI output is plain English progress, not technical log noise
- Never require the user to navigate into nested directories to find output

## Directory structure

```
yt-dlp-channel/
├── CLAUDE.md               # this file
├── README.md               # user-facing docs
├── config.py               # all configuration variables
├── agent.py                # CLI entrypoint
├── db.py                   # SQLite helpers (scoped per company)
├── phases/
│   ├── discover.py         # yt-dlp metadata fetch + date filter
│   ├── download.py         # audio-only download via yt-dlp -x
│   ├── transcribe.py       # calls `transcribe` subprocess
│   └── synthesize.py       # Claude API: per-video → cross-video report
├── reports/                # ← user opens this; one .md file per company run
└── .workspace/             # hidden scratch space — user never touches this
    └── <company-slug>/
        ├── audio/
        ├── transcripts/
        ├── channel.db
        └── canvas-<date>.json  # machine-readable canvas for future compare step
```

## Key configuration variables (`config.py`)

| Variable | Default | Notes |
|---|---|---|
| `LOOKBACK_MONTHS` | `30` | How far back to pull videos (~2.5 years). Always computed dynamically from today's date — never hardcode a year. |
| `WHISPER_MODEL` | `medium.en` | Options: tiny.en, base.en, small.en, medium.en, large-v3 |
| `AUDIO_FORMAT` | `m4a` | Audio container for yt-dlp extraction |
| `LLM_MODEL` | `gpt-4o-mini` | Model used for synthesis phases |
| `DATA_DIR` | `.workspace` | Root for all pipeline scratch data |
| `REPORTS_DIR` | `reports` | Where final reports land |

## System dependencies (pre-installed on user's machine)

- `yt-dlp` — video/audio download
- `whisper` — Whisper wrapper at `~/bin/whisper`; usage: `whisper <file> [--fast] [--model tiny.en|base.en|small.en|medium.en|large-v3] [--output-dir <dir>]`
- `ffmpeg` — audio processing
- `python3` (3.13)

## Pipeline phases

1. **Discover** — `yt-dlp --flat-playlist --dump-json`, filtered by `--dateafter` computed from `LOOKBACK_MONTHS`
2. **Download** — `yt-dlp -x --audio-format m4a` per video; skips already-downloaded
3. **Transcribe** — `transcribe <audio> --model medium.en --output-dir ...` per file; skips already-transcribed
4. **Synthesize** — two OpenAI API passes:
   - Pass 1: per-video structured JSON with 8 keys: `customer_problems`, `product_philosophy`, `strategic_bets`, `market_framing`, `competitive_signals`, `customer_voices`, `notable_quotes`, `product_mentions`. Every claim requires a verbatim quote anchor.
   - Pass 2: cross-video canvas JSON with 7 fixed sections (problem obsession → who they're building for → how they decide → where they're placing bets → category framing → what's shifted → what they're not saying). Canvas saved to `.workspace/`; human report rendered from canvas and saved to `reports/`.

## SQLite state machine

Each video row: `video_id | title | published | duration | status | audio_path | transcript_path | summary_json`

Status flow: `discovered → downloaded → transcribed → analyzed`

Re-running the agent skips any video already at or past a given stage.

## Date handling

All date filters must be computed dynamically from `LOOKBACK_MONTHS` and `datetime.now()`. Never hardcode a year. When building search queries that need recency, use a rolling window that always ends at the current year.

## .gitignore

`.workspace/` must be in `.gitignore` — it holds audio files and will be gigabytes in size.

## Example company

Productside — `https://www.youtube.com/@productside/videos`
Product management training and coaching company. Used as the reference example throughout docs and tests.
