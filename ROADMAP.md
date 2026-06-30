# Roadmap

Ideas and planned improvements for future versions. Not in any particular order — priority will be driven by what makes the reports more useful for product managers.

---

## Incremental updates

**What:** Right now every run re-scans the full 30-month lookback window. Once a company has been captured, subsequent runs should only pull what's new since the last run.

**How it would work:**
- Store `last_run_date` per company in `channel.db`
- On re-run, set `--dateafter` to `last_run_date` instead of `LOOKBACK_MONTHS` back
- Only download and transcribe newly published videos
- Re-run Pass 2 synthesis to fold new content into an updated canvas and report
- Diff the new canvas against the previous one to surface what changed

**Why it matters:** A 30-minute first run becomes a 2-minute refresh. Companies that publish frequently (weekly podcasts, product launches) become much easier to track continuously.

---

## Parallel downloads and transcription

**What:** Downloads and transcription currently run one video at a time, sequentially. Both phases could run multiple jobs at once.

**How it would work:**
- Download phase: use `concurrent.futures.ThreadPoolExecutor` to run multiple `yt-dlp` processes simultaneously (3–5 at a time is safe without hitting rate limits)
- Transcription phase: run multiple `whisper` processes in parallel (limited by CPU/RAM — each whisper process is heavy)
- DB writes need a lock to stay thread-safe under concurrent access

**Why it matters:** A 50-video channel that takes 60 minutes to transcribe could finish in 15–20 minutes with parallel whisper jobs on a modern machine.

---

## Smaller audio files

**What:** Whisper only needs 16kHz mono audio to transcribe accurately. We're currently storing stereo m4a files at full quality, which is 4–6× larger than necessary.

**How it would work:**
- Add an `ffmpeg` post-processing step after download to convert to 16kHz mono mp3 or wav
- Or pass `--postprocessor-args` to yt-dlp to do it in one step
- Target: ~24–48 kbps mono instead of 128–192 kbps stereo
- Expected storage reduction: 60–75% per file

**Why it matters:** A 50-video channel currently uses 2–4 GB. With this change it would use 500 MB–1 GB. Makes the tool practical on machines with limited storage.

---

## Podcast and RSS ingestion

**What:** Extend the pipeline beyond YouTube to include podcast feeds and other public audio sources. Many companies publish the same content (or exclusive content) as podcasts.

**How it would work:**
- New phase: `phases/ingest_rss.py` — parses a podcast RSS feed, extracts episode metadata and audio URLs, downloads audio directly
- Same whisper → Pass 1 → Pass 2 pipeline applies unchanged
- `agent.py` would accept either a YouTube URL or an RSS feed URL and route accordingly
- Episode title and publish date come from RSS `<item>` metadata

**Why it matters:** Some of the most candid company content lives in podcast form — founder interviews, customer stories, earnings call recaps. This doubles the signal surface without changing the output format.

---

## Vector database and search (RAG)

**What:** Embed all captured transcripts and Pass 1 summaries into a vector database so you can ask natural language questions across everything the tool has captured.

**How it would work:**
- After transcription, chunk each transcript and embed using OpenAI embeddings API
- Store in a local vector DB (Chroma or FAISS — no server required)
- New CLI command: `python3 agent.py --search "what has [company] said about pricing?"`
- Could support cross-company queries: "which of my captured companies mentions enterprise sales?"
- Canvas JSON would also be embedded to enable insight-level search, not just transcript search

**Why it matters:** Right now you can only search within a single report. With RAG, the entire corpus of captured companies becomes queryable — turning the tool from a report generator into a research database.

---

## Transcript frontmatter

**What:** Transcript `.txt` files currently contain raw text with no metadata. Adding a frontmatter header makes them self-documenting and useful outside the pipeline.

**How it would work:**
- After transcription, prepend a YAML header to each `.txt` file:

```
---
video_id: dQw4w9WgXcQ
title: "What Great PMs Actually Do"
channel: productside
published: 2025-03-15
duration: 1842
url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
---

[transcript text follows]
```

- Whisper step writes the frontmatter using metadata already in the DB row
- Transcripts become importable into Obsidian, Notion, or any tool that reads markdown with frontmatter

**Why it matters:** Makes the `.workspace/` transcripts useful as a standalone research artifact, not just pipeline scratch data. A PM could search or browse transcripts directly without going through the report.

---

## Report quality (ongoing)

**What:** The synthesis prompts and canvas schema will continue to evolve as we learn what product managers actually need.

**Known gaps to address:**
- `not_saying` section tends to surface only one gap; should enumerate three to five
- `building_for` sometimes drifts toward demographics instead of mindset and JTBD
- `placing_bets` rarely surfaces the "what breaks if the assumption is wrong" angle
- Cross-video aggregation in Pass 1 is not yet fully de-duplicated before Pass 2

**Possible upgrades:**
- Upgrade synthesis model from `gpt-4o-mini` to `gpt-4o` for the Pass 2 step only (better reasoning, modest cost increase)
- Add a Pass 1.5 aggregation step that clusters and de-duplicates signals across all videos before Pass 2 — would reduce noise in the synthesis input
- Add confidence scoring to canvas claims so the report can visually distinguish high-signal patterns from thin evidence

---

## Company comparison mode

**What:** Run two or more canvases side-by-side to surface where companies agree, diverge, or talk past each other.

**How it would work:**
- New command: `python3 agent.py --compare companyA companyB`
- Load both `canvas-<date>.json` files and send to a new Pass 3 prompt
- Output: a comparison report with a grid of how each company answers the nine canvas sections
- Highlight: same problem framing (convergent market belief), opposite category framing (direct competitive tension), or one company saying what the other isn't

**Why it matters:** This is the original reason the canvas schema uses fixed section keys. Once two canvases exist, comparison is essentially a prompt away.
