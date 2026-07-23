# Roadmap

## Approved execution phases

This sequence is the active delivery plan. The older Now / Next / Later
horizons below remain useful as a feature backlog, but phase gates determine
what happens next.

### Phase 0 — Document and checkpoint the implemented system

**Goal:** Make the current work reproducible and restartable before adding
another feature.

- [x] Update the user-facing `README.md`.
- [x] Add repository-level `AGENTS.md`.
- [x] Refresh `CLAUDE.md` for company and topical modes.
- [x] Add `docs/current-state.md` as the evidence-backed restart guide.
- [x] Reconcile the roadmap with the agreed phase sequence.
- [x] Document the queue, taxonomy, retrieval, exports, notebook, results,
  limitations, and next gates.
- [x] Verify the implementation and notebook.
- [x] Confirm the GitHub repository is public.
- [x] Commit the complete checkpoint and push it to `main`.

**Exit gate:** Documentation matches the live implementation, checks pass, the
remote repository is public, and `origin/main` contains the Phase 0 commit.

### Phase 1 — Repair company-intelligence report quality

1. Regenerate the included sample report from a validated canvas.
2. Require usable quote, video, and date attribution in evidence-bearing
   sections.
3. Preserve `not_saying` as the explicitly labeled inference exception.
4. Add a release check for the report evidence contract.

### Phase 2 — Review and scope the topical foundation

1. Review a stratified sample of the twenty-case v0.3 labels in the notebook.
2. Record corrections and decide whether the taxonomy needs a version bump.
3. Add retrieval scope by case set, industry, case role, and playlist range.
4. Keep the original regression suite unchanged and separate from expansion
   suites.

### Phase 3 — Build the pedagogic learning layer

1. Generate source-linked case cards for all twenty cases.
2. Generate causal chains that distinguish source claims from inference.
3. Create a cross-case pattern matrix.
4. Create teaching notes with lessons, counterexamples, boundary conditions,
   discussion questions, and evidence gaps.
5. Add pedagogic evaluations for patterns, counterexamples, and boundaries.

### Phase 4 — Add trustworthy synthesis and corroboration

1. Add source-backed answer synthesis after scoped retrieval passes review.
2. Label unsupported generalization and analyst inference.
3. Run a small corroboration pilot using a second source.
4. Do not call the corpus domain intelligence until corroboration is present.

### Phase 5 — Expand through reviewed batches

1. Capture playlist positions 21–35.
2. Review sponsor boundaries, transcript quality, taxonomy drift, retrieval
   coverage, and new patterns.
3. Relabel affected passages and build a new disposable collection when needed.
4. Continue through the playlist in gated batches of 15–20 videos.

### Phase 6 — Improve portable study surfaces

1. Package data-only archives containing manifests, canonical transcripts,
   taxonomy, evaluations, exports, and the notebook.
2. Support Jupyter, Google Colab, Google Antigravity, pandas, Polars, and
   DuckDB without requiring private API keys for exploration.
3. Exclude audio and generated Chroma indexes from portable archives.

### Phase 7 — Extend into domain intelligence

1. Apply the topical architecture across multiple channels, companies, and
   source types.
2. Add source comparison, contradiction tracking, and corroboration.
3. Build domain-level patterns only after the topical review workflow is
   trustworthy.

---

Three time horizons. Each builds on the one before it.

| Horizon | Theme | Focus |
|---|---|---|
| **Now** | Speed & Size Optimization | Make the pipeline faster and leaner on any machine |
| **Next** | Expand & Refine Sources | More signal, cleaner data, better output quality |
| **Later** | Recall & Query Captures | Turn the corpus into a searchable, explorable knowledge base |

---

## Now — Speed & Size Optimization

### Smaller audio files *(do this first)*

**What:** Whisper only needs 16kHz mono audio to transcribe accurately. We're currently storing stereo m4a files at full quality — 4–6× larger than necessary. Shrink the files first so that parallel jobs are processing lean data, not bloated originals.

**How it would work:**
- Add an `ffmpeg` post-processing step after download to convert to 16kHz mono mp3 or wav
- Or pass `--postprocessor-args` to yt-dlp to do it in one step
- Target: ~24–48 kbps mono instead of 128–192 kbps stereo
- Expected storage reduction: 60–75% per file

**Why it matters:** A 50-video channel currently uses 2–4 GB. With this change it drops to 500 MB–1 GB. There's no point spinning up parallel whisper jobs if each one is chewing through 80 MB files instead of 20 MB files — get the file size right first, then parallelize.

---

### Parallel downloads and transcription *(do this second)*

**What:** Downloads and transcription currently run one video at a time, sequentially. Both phases could run multiple jobs at once. Do this after smaller audio files so parallelism compounds the storage and speed gains.

**How it would work:**
- Download phase: use `concurrent.futures.ThreadPoolExecutor` to run multiple `yt-dlp` processes simultaneously (3–5 at a time without hitting rate limits)
- Transcription phase: run multiple `whisper` processes in parallel (limited by CPU/RAM — each whisper process is heavy)
- DB writes need a lock to stay thread-safe under concurrent access

**Why it matters:** A 50-video channel that takes 60 minutes to transcribe could finish in 15–20 minutes with parallel whisper jobs — and those gains compound when the files are already lean from the step above.

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
- The included sample report does not display the verbatim evidence quotes promised by the report contract. Regenerate it from a validated canvas and add a release check that fails when evidence-bearing sections contain claims without usable quote, video, and date attribution. `not_saying` remains the explicitly labeled inference exception.
- `not_saying` section tends to surface only one gap; should enumerate three to five
- `building_for` sometimes drifts toward demographics instead of mindset and JTBD
- `placing_bets` rarely surfaces the "what breaks if the assumption is wrong" angle
- Cross-video aggregation in Pass 1 is not yet fully de-duplicated before Pass 2

**Possible upgrades:**
- Upgrade synthesis model from `gpt-4o-mini` to `gpt-4o` for Pass 2 only (better reasoning, modest cost increase)
- Add a Pass 1.5 aggregation step that clusters and de-duplicates signals across all videos before Pass 2
- Add confidence scoring to canvas claims so the report can distinguish high-signal patterns from thin evidence

---

### Topical intelligence — twenty-video calibration corpus

**What:** Add a topical corpus mode alongside company intelligence. Instead of asking, "What is this company trying to do?", topical mode asks, "What can we learn across a body of material about this subject, and where did each finding come from?"

**Calibration status (2026-07-23):** Twenty videos are captured and transcribed; all 121 playlist entries are materialized in the durable SQLite queue. Taxonomy v0.3 distinguishes failure and decline from turnaround, resilience, partial recovery, and values-tradeoff cases. The local index contains 334 content passages and excludes 54 reviewed sponsor passages. Hybrid retrieval scores 5/10 strict and 5/10 complete case coverage on the unchanged three-case regression, and 8/10 strict plus 8/10 complete case coverage on the new twenty-video calibration suite. Portable CSV, JSONL, and Parquet exports plus a Colab-ready notebook are complete. Details are in [`docs/topical-intelligence/business-failures-spike.md`](docs/topical-intelligence/business-failures-spike.md) and [`docs/topical-intelligence/scale-and-learning-plan.md`](docs/topical-intelligence/scale-and-learning-plan.md).

**Next gate:** Do not start another capture batch yet. Add explicit query scope or conversational case context, review a stratified sample of v0.3 labels in the notebook, and generate case cards plus causal chains for the twenty cases. Keep the original regression unchanged and report it separately from expansion suites.

The calibration corpus uses the first twenty videos from this business-failures playlist:

`https://www.youtube.com/playlist?list=PLZ6vahBdAJ3iArMOb5Mrpav98SjW9dsaz`

The playlist URL already works with the current YouTube discovery and download path. The new work is the transcript format, topic-aware enrichment, retrieval index, and query experience.

**Why grow from ten to twenty:** The second batch tested the durable queue,
portable analysis path, and whether the taxonomy could represent counterexamples.
It exposed a necessary `case_role` dimension: Crocs is a turnaround and Panda
Express is a resilience case, not a failure that should be forced into negative
labels.

**Architecture boundary:**
- Keep company intelligence as an intact report mode; do not replace its two-pass canvas.
- Share discovery, download, transcription, SQLite resume state, and source metadata across modes.
- Give topical mode its own enrichment and retrieval stages.
- Make topical captures relevance-bounded by playlist or explicit selection, not automatically limited by the company-oriented 30-month lookback.
- Treat domain intelligence across multiple companies and sources as a later mode built on the topical foundation.

**Proof-of-learning sequence:**

1. **Capture twenty source videos**
   - Use an explicit `--limit 20` capture boundary while materializing the full playlist queue.
   - Preserve the original audio, raw transcript, timestamped subtitle output, title, publication date, duration, video ID, playlist ID, channel, and YouTube URL.
   - Do not generate the existing company-intelligence report for this run.

2. **Inspect before categorizing**
   - Read the transcripts as a set and identify recurring ways business failure is described.
   - Begin with candidate labels such as company or subject, industry, failure stage, precipitating event, contributing factors, decisions, outcomes, warning signals, and evidence type.
   - Record unclear or overlapping labels instead of forcing every passage into a category.
   - Human-review the proposed taxonomy before applying it to more videos.

3. **Write canonical transcript records**
   - Store each transcript as Markdown with YAML frontmatter, following the proven metadata-preservation pattern in `lennysan-rag-o-matic`.
   - Include stable source fields plus `corpus_type`, `corpus_slug`, `topic`, `keywords`, `taxonomy_version`, and the reviewed topic labels.
   - Keep raw transcript text separate from generated labels so the source can be reprocessed when the taxonomy changes.

4. **Build a local retrieval index**
   - Chunk transcripts with overlap and copy the full source metadata onto every chunk.
   - Preserve each chunk's start and end timestamps so citations can deep-link to the relevant moment in the video.
   - Use local `sentence-transformers/all-MiniLM-L6-v2` embeddings and a separate Chroma collection per corpus.
   - Use MMR-style retrieval to reduce near-duplicate results.
   - Keep the generated vector index disposable and rebuildable from the canonical Markdown transcripts.

5. **Add a cited query path**
   - Support questions such as, "What warning signs appeared before these businesses failed?" or "Which failures involved premature expansion?"
   - Return a direct synthesis, distinguish source-backed findings from inference, and show the video title, date, URL, and relevant excerpt for every answer.
   - Refuse to generalize beyond the captured evidence without labeling the limitation.

6. **Decide whether to scale**
   - Review retrieval quality, label usefulness, attribution, and unanswered questions.
   - Revise and version the taxonomy.
   - Only then ingest the rest of the playlist and add incremental indexing.

**Suggested workspace shape:**

```text
.workspace/
  topics/
    business-failures/
      corpus.json
      channel.db
      audio/
      transcripts/
        <video-id>/
          raw.txt
          transcript.md
      index/
        chroma_db/
```

**Proof-of-learning success criteria:**
   - Twenty videos can be captured and resumed without disturbing existing company workspaces.
- Every transcript has complete, human-readable source metadata.
- The initial taxonomy is documented as versioned workup, not permanent truth.
- A query retrieves relevant passages from more than one video when appropriate.
- Every synthesized answer links back to the exact source videos, timestamps, and excerpts.
- Rebuilding the vector index does not require downloading or transcribing again.

**Not in the first slice:** full-playlist ingestion, automated taxonomy finalization, domain-level company comparison, a Streamlit interface, or a polished topical report. The first outcome is a trustworthy mini knowledge base we can learn from.

---

### Podcast and alternative source ingestion

**What:** Extend the pipeline beyond YouTube channel URLs to support podcasts, specific playlists used as recurring series, and any audio source a company publishes regularly.

**Sources to support:**

| Source | Example | How |
|---|---|---|
| YouTube podcast tab | `https://www.youtube.com/@LennysPodcast/podcasts` | Already works via yt-dlp — same as `/videos` |
| YouTube playlist as series | `https://www.youtube.com/playlist?list=PLxxx` | Already works — slug derived from `list=` param |
| Podcast RSS feed | `https://feeds.transistor.fm/lenny-s-podcast` | New `phases/ingest_rss.py` — parse feed, download audio directly |
| Podcast site audio | Direct `.mp3` / `.m4a` URL | yt-dlp handles most cases; fallback to direct HTTP download |

**What's already working today:** YouTube channel tabs (including `/podcasts`) and playlist URLs work without any changes — yt-dlp handles them. Small playlists (even 20 videos over 3 years) are fully captured since `MAX_VIDEOS=50` and the 30-month window are both generous enough not to cut anything off.

**What needs building:** RSS feed ingestion for sources that live outside YouTube. A podcast published on Spotify, Apple Podcasts, or a company's own site won't have a YouTube URL — the RSS feed is the only reliable way to reach it.

**How RSS ingestion would work:**
- New phase: `phases/ingest_rss.py` — parses an RSS feed, extracts episode metadata and enclosure audio URLs, downloads directly
- Same whisper → Pass 1 → Pass 2 pipeline applies unchanged
- `agent.py` accepts either a YouTube URL or an RSS feed URL and routes accordingly
- Episode title and publish date come from RSS `<item>` metadata

**Why it matters:** Some of the most candid company content lives outside YouTube — founder interviews, earnings call recaps, customer stories. Supporting RSS means one command can ingest a company's entire public audio footprint, not just what they've posted on YouTube.

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
