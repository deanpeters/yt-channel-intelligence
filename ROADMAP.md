# Roadmap

Three time horizons. Each builds on the one before it.

| Horizon | Theme | Focus |
|---|---|---|
| **Now** | Speed & Size Optimization | Make the pipeline faster and leaner on any machine |
| **Next** | Expand & Refine Sources | More signal, cleaner data, better output quality |
| **Later** | Recall & Query Captures | Turn the corpus into a searchable, explorable knowledge base |

---

## Now — Speed & Size Optimization

### Parallel downloads and transcription

**What:** Downloads and transcription currently run one video at a time, sequentially. Both phases could run multiple jobs at once.

**How it would work:**
- Download phase: use `concurrent.futures.ThreadPoolExecutor` to run multiple `yt-dlp` processes simultaneously (3–5 at a time without hitting rate limits)
- Transcription phase: run multiple `whisper` processes in parallel (limited by CPU/RAM — each whisper process is heavy)
- DB writes need a lock to stay thread-safe under concurrent access

**Why it matters:** A 50-video channel that takes 60 minutes to transcribe could finish in 15–20 minutes with parallel whisper jobs on a modern machine.

---

### Smaller audio files

**What:** Whisper only needs 16kHz mono audio to transcribe accurately. We're currently storing stereo m4a files at full quality — 4–6× larger than necessary.

**How it would work:**
- Add an `ffmpeg` post-processing step after download to convert to 16kHz mono mp3 or wav
- Or pass `--postprocessor-args` to yt-dlp to do it in one step
- Target: ~24–48 kbps mono instead of 128–192 kbps stereo
- Expected storage reduction: 60–75% per file

**Why it matters:** A 50-video channel currently uses 2–4 GB. With this change it drops to 500 MB–1 GB. Makes the tool practical on machines with limited storage.

---

### Incremental updates

**What:** Right now every run re-scans the full 30-month lookback window. Once a company has been captured, subsequent runs should only pull what's new since the last run.

**How it would work:**
- Store `last_run_date` per company in `channel.db`
- On re-run, set `--dateafter` to `last_run_date` instead of `LOOKBACK_MONTHS` back
- Only download and transcribe newly published videos
- Re-run Pass 2 synthesis to fold new content into an updated canvas and report
- Diff the new canvas against the previous one to surface what changed

**Why it matters:** A 30-minute first run becomes a 2-minute refresh. Companies that publish frequently become easy to track continuously.

---

## Next — Expand & Refine Sources

### Transcript frontmatter

**What:** Transcript `.txt` files currently contain raw text with no metadata. Adding a frontmatter header makes them self-documenting, cleanly labeled, and useful outside the pipeline.

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
keywords:
  - product discovery
  - outcome-driven
  - stakeholder alignment
  - jobs to be done
categories:
  - product philosophy
  - customer research
---

[transcript text follows]
```

- Identity fields (video_id, title, channel, published, duration, url) come from metadata already in the DB row — written immediately after transcription
- Keywords are extracted by a lightweight Pass 0.5 LLM call on the transcript — a cheap, fast prompt that pulls the 4–8 most meaningful terms
- Categories map to a fixed taxonomy (e.g. product philosophy, customer research, competitive signal, market framing, product launch, customer story, technical deep-dive) — the same Pass 0.5 call classifies each video into one or more categories
- Both fields make transcripts filterable and groupable before the vector database exists, and become richer metadata for embedding once it does
- Transcripts become importable into Obsidian, Notion, or any tool that reads markdown with frontmatter

**Why it matters:** Keywords and categories turn a folder of raw transcripts into an organized, searchable library. A PM could open `.workspace/productside/transcripts/` and immediately see which videos are about competitive signals, which are customer stories, and which cover product philosophy — without reading a single transcript.

---

### Report quality (ongoing)

**What:** The synthesis prompts and canvas schema will continue to evolve as we learn what product managers actually need.

**Known gaps to address:**
- `not_saying` section tends to surface only one gap; should enumerate three to five
- `building_for` sometimes drifts toward demographics instead of mindset and JTBD
- `placing_bets` rarely surfaces the "what breaks if the assumption is wrong" angle
- Cross-video aggregation in Pass 1 is not yet fully de-duplicated before Pass 2

**Possible upgrades:**
- Upgrade synthesis model from `gpt-4o-mini` to `gpt-4o` for Pass 2 only (better reasoning, modest cost increase)
- Add a Pass 1.5 aggregation step that clusters and de-duplicates signals across all videos before Pass 2
- Add confidence scoring to canvas claims so the report can distinguish high-signal patterns from thin evidence

---

### Podcast and RSS ingestion

**What:** Extend the pipeline beyond YouTube to include podcast feeds and other public audio sources. Many companies publish the same content — or exclusive content — as podcasts.

**How it would work:**
- New phase: `phases/ingest_rss.py` — parses a podcast RSS feed, extracts episode metadata and audio URLs, downloads audio directly
- Same whisper → Pass 1 → Pass 2 pipeline applies unchanged
- `agent.py` accepts either a YouTube URL or an RSS feed URL and routes accordingly
- Episode title and publish date come from RSS `<item>` metadata

**Why it matters:** Some of the most candid company content lives in podcast form — founder interviews, customer stories, earnings call recaps. This doubles the signal surface without changing the output format.

---

## Later — Recall & Query Captures

### Vector database and semantic search

**What:** Embed all captured transcripts and Pass 1 summaries into a vector database so you can ask natural language questions across everything the tool has captured.

**How it would work:**
- After transcription, chunk each transcript and embed using OpenAI embeddings API
- Store in a local vector DB (Chroma or FAISS — no server required)
- New CLI command: `python3 agent.py --search "what has [company] said about pricing?"`
- Supports cross-company queries: "which of my captured companies mentions enterprise sales?"
- Canvas JSON also embedded to enable insight-level search, not just transcript search

**Why it matters:** Right now you can only search within a single report. With semantic search, the entire corpus of captured companies becomes queryable — turning the tool from a report generator into a research database.

---

### Company comparison mode

**What:** Run two or more canvases side-by-side to surface where companies agree, diverge, or talk past each other.

**How it would work:**
- New command: `python3 agent.py --compare companyA companyB`
- Load both `canvas-<date>.json` files and send to a new Pass 3 prompt
- Output: a comparison report mapping how each company answers the nine canvas sections
- Highlights: same problem framing (convergent market belief), opposite category framing (direct competitive tension), one company saying what the other isn't

**Why it matters:** This is the original reason the canvas schema uses fixed section keys. Once two canvases exist, comparison is a prompt away.

---

### Streamlit exploration UI *(requires vector database)*

**What:** A lightweight web interface that lets a PM explore everything they've captured — transcripts, insights, and canvas sections — through natural language questions and visual navigation. No terminal required once it's running.

**Two modes:**

*Channel mode* — focused on a single company:
- Browse canvas sections interactively (click into any claim to see all supporting evidence)
- Ask free-form questions: "What has this company said about enterprise customers?" or "Show me every time they mention pricing"
- Timeline view of how messaging has shifted across the capture window
- Jump from insight to source transcript in one click

*Corpus mode* — across all captured companies:
- Ask questions that span the full database: "Which of my companies mention AI most often?" or "Where do these companies agree on customer problems?"
- Side-by-side canvas comparison
- Gap analysis: "What is everyone in this space not saying?"

**How it would work:**
- Built with Streamlit — Python only, no frontend knowledge required, runs locally
- Reads from the vector database for semantic search
- Reads from canvas JSON files for structured section navigation
- Launch with: `python3 app.py` — opens in the browser automatically

**Why it matters:** The more companies you capture, the more valuable the corpus becomes. The Streamlit UI turns accumulated intelligence into an explorable research tool — and removes the terminal entirely for day-to-day use.
