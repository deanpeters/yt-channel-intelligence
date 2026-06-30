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
yt-channel-intelligence/
├── CLAUDE.md               # this file
├── README.md               # user-facing docs
├── SETUP.md                # first-time setup guide (OpenAI key, dependencies)
├── USING-YOUR-REPORT.md    # PM guide to reading and acting on reports
├── ROADMAP.md              # Now / Next / Later feature roadmap
├── config.py               # all configuration variables
├── agent.py                # CLI entrypoint
├── db.py                   # SQLite helpers (scoped per company)
├── phases/
│   ├── discover.py         # yt-dlp metadata fetch + date filter
│   ├── download.py         # audio-only download via yt-dlp -x
│   ├── transcribe.py       # calls `whisper` subprocess
│   ├── synthesize.py       # OpenAI API: per-video → cross-video report
│   └── synthesize.template.md  # prompt design doc and canonical examples
├── setup.sh                # Mac first-time setup script
├── setup.bat               # Windows first-time setup script
├── reports/                # ← user opens this; one .md file per company run
└── .workspace/             # hidden scratch space — user never touches this
    └── <company-slug>/
        ├── audio/
        ├── transcripts/
        ├── channel.db
        └── canvas-<date>.json  # machine-readable canvas for compare/RAG
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
4. **Synthesize** — two OpenAI `gpt-4o-mini` passes. Role is "strategic advisor for PM leaders" — produce insights, not data summaries. Every claim requires a verbatim quote anchor.
   - Pass 1: per-video structured JSON with 8 keys: `customer_problems`, `product_philosophy`, `strategic_bets`, `market_framing`, `competitive_signals`, `customer_voices`, `notable_quotes`, `product_mentions`.
   - Pass 2: cross-video canvas with a top-level `executive_summary` prose block plus 9 fixed sections: `product_line` (exhaustive inventory), `problem_obsession`, `building_for`, `how_they_decide`, `placing_bets`, `category_framing`, `momentum_tone` (ON OFFENSE / ON DEFENSE verdict), `whats_shifted`, `not_saying` (most valuable section — name the absence, state the strategic implication). Canvas saved to `.workspace/<slug>/canvas-<date>.json`; human report rendered from canvas and saved to `reports/`.
   - Collapse aggressively: one claim with `signal_strength 15` beats fifteen claims with `signal_strength 1`.
   - Renderer filters any evidence item whose quote starts with "no quote" (case-insensitive).

## SQLite state machine

Each video row: `video_id | title | published | duration | status | audio_path | transcript_path | summary_json`

Status flow: `discovered → downloaded → transcribed → analyzed`

Re-running the agent skips any video already at or past a given stage.

## Date handling

All date filters must be computed dynamically from `LOOKBACK_MONTHS` and `datetime.now()`. Never hardcode a year. When building search queries that need recency, use a rolling window that always ends at the current year.

## LLM provider

**OpenAI only. Never use the Anthropic / Claude API in this project.**

`OPENAI_API_KEY` must be sourced from environment variables — never hardcoded in any file. The key is set once at shell level (`~/.zshrc` on Mac, System Environment Variables on Windows) and read at runtime via `os.environ`. Any code that touches LLM calls must use the `openai` Python package with `gpt-4o-mini` as the default model.

## Security

All secrets (API keys) come from environment variables only. No `.env` files, no hardcoded strings, no secrets in any committed file.

## .gitignore

`.workspace/` must be in `.gitignore` — it holds audio files and will be gigabytes in size. Also excludes `reports/`, `__pycache__/`, `*.pyc`, `.DS_Store`, and `.claude/`.

## Roadmap

See `ROADMAP.md` for the Now / Next / Later feature plan. Current priority order within **Now**:
1. Smaller audio files (16kHz mono, 60–75% storage reduction) — do this first
2. Parallel downloads and transcription — compounds the size gains
3. Incremental updates (track last-run date per company)

## Example company

Productside — `https://www.youtube.com/@productside/videos`
Product management training and coaching company. Used as the reference example throughout docs and tests.
