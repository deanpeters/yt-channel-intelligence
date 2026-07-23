# Current State and Restart Guide

**Checkpoint:** Phase 0 complete. Phase 2 tooling in progress: retrieval
scoping and the stratified label-review harness are implemented; the human
label audit and taxonomy-bump decision are still pending.

**Updated:** 2026-07-23

**Branch:** `main`

**Repository policy:** public
**Remote verification:** GitHub confirmed public on 2026-07-23

## What this project is now

Channel Intelligence began as a company-intelligence report generator for
public YouTube channels. It now supports a second, experimental topical mode
that turns a bounded playlist into a traceable research corpus.

The modes share discovery, audio capture, transcription, SQLite state, and
source metadata. They intentionally diverge after transcription:

```text
company source -> per-video analysis -> cross-video canvas -> report

topical source -> canonical transcripts -> versioned enrichment
               -> disposable retrieval index -> query, evaluation, and exports
```

The next architectural destination is domain intelligence across multiple
channels, companies, and source types. That work should build on the topical
mode only after its review and corroboration workflow is trustworthy.

## Implemented company-intelligence workflow

- Accepts public channel, courses-tab, and playlist URLs.
- Discovers recent substantive videos using a rolling 30-month lookback.
- Downloads audio and transcribes it with configurable Whisper models.
- Uses LiteLLM for provider-neutral analysis and synthesis.
- Produces a structured canvas and a Markdown report.
- Resumes completed discovery, download, transcription, and analysis work.

The sample report still needs regeneration so its visible evidence matches the
report contract. That is Phase 1.

## Implemented topical-intelligence workflow

### Capture and queue

- `agent.py --mode topic` materializes the full playlist into SQLite.
- `--limit` creates a safe capture boundary without losing later queue items.
- Download workers, randomized pauses, retry timing, attempt history, worker
  IDs, and stale-claim recovery are implemented.
- Database writes remain serialized in the controlling process.
- Local transcription remains serial to avoid memory contention.

### Canonical corpus and enrichment

- Raw transcript text remains unchanged.
- Canonical Markdown preserves source metadata and timestamps.
- Enrichment lives in versioned JSONL derived from the canonical corpus.
- Sponsor intervals and labels can be reviewed independently.
- Same-version labels can be reused; taxonomy changes make records eligible for
  relabeling.
- A stratified label-review harness (`review-sample` / `review-apply`) samples
  passages into a worksheet and converts reviewer corrections into
  `passage_overrides`. Overrides can now add labels, remove wrong labels, and
  correct epistemic status. Machine labels remain unaudited until reviewed.
- Enrichment also writes human-readable navigation aids into the workspace: a
  `<SUBJECT>.md` marker file next to each video's `transcript.md`, and a
  top-level `INDEX.md` listing every case by subject, case role, industry,
  and video ID.

### Retrieval and evaluation

- Chroma uses local sentence-transformer embeddings.
- Retrieval combines semantic similarity with case, mechanism, causal-role,
  passage-label, and case-role signals.
- Queries can be scoped to part of the corpus by industry, case role, specific
  case (video ID or subject substring), and playlist range. Scope is applied as
  a metadata filter before hybrid ranking; each passage carries its
  `playlist_index` for range filtering.
- Passage timestamps support direct YouTube links.
- Sponsor material is excluded before indexing.
- The original evaluation suite remains fixed instead of being tuned to the
  expanded corpus.
- Expansion suites are versioned separately.

### Portable analysis

The export command creates:

- `cases.csv`
- `case_mechanisms.csv`
- `passages.csv`
- `passages.jsonl`
- `passages.parquet`
- `export-manifest.json`

The exploration notebook reads these exports rather than SQLite or Chroma. It
works locally with the registered **YT Channel Intelligence (topic)** kernel
and can be used in Google Colab or Google Antigravity by pointing it at the
export directory.

## Business-failures calibration evidence

Source playlist:

`https://www.youtube.com/playlist?list=PLZ6vahBdAJ3iArMOb5Mrpav98SjW9dsaz`

Current local checkpoint:

| Measure | Result |
|---|---:|
| Playlist entries queued | 121 |
| Cases captured and transcribed | 20 |
| Cases awaiting later batches | 101 |
| Transcribed words | 73,181 |
| Taxonomy | `0.3-workup` |
| Total passages | 388 |
| Sponsor passages excluded | 54 |
| Indexed passages | 334 |
| Unlabeled passages | 0 |
| Fixed regression score | 5/10 |
| Twenty-case calibration score | 8/10 |
| Sponsor leakage | 0 |

The fixed regression drop is informative: questions originally written around
three cases are underspecified once twenty valid cases compete for six result
slots. The next retrieval improvement is explicit query scope or conversational
case context, not hidden tuning to old expected answers.

The twenty cases also exposed the need for `case_role`. Crocs is a turnaround
counterexample and Panda Express is a resilience counterexample; neither should
be forced into a failure label merely because it appears in the playlist.

## Reproducible commands

Capture or safely resume the calibration boundary:

```bash
python3 agent.py \
  --mode topic \
  --topic "Business failures" \
  --limit 20 \
  --whisper-model small.en \
  --download-workers 2 \
  --download-sleep-min 3 \
  --download-sleep-max 8 \
  "https://www.youtube.com/playlist?list=PLZ6vahBdAJ3iArMOb5Mrpav98SjW9dsaz"
```

Rebuild derived material without downloading again:

```bash
bash setup-topic.sh
.venv-topic/bin/python topic_corpus.py enrich
.venv-topic/bin/python topic_corpus.py index
.venv-topic/bin/python topic_corpus.py export
```

Run evaluations:

```bash
.venv-topic/bin/python topic_corpus.py evaluate
.venv-topic/bin/python topic_corpus.py evaluate \
  --questions evaluations/business-failures-calibration-questions.yaml \
  --output reports/topics/business-failures-calibration-evaluation.md
```

## Durable and disposable artifacts

| Layer | Durable? | Committed? |
|---|---|---|
| Source and workflow code | Yes | Yes |
| Taxonomy and evaluation questions | Yes | Yes |
| Canonical transcript schema and logic | Yes | Yes |
| Raw audio and transcripts | Local source cache | No |
| SQLite queue and attempt history | Local operational state | No |
| Versioned enrichment output | Rebuildable local artifact | No |
| Chroma index | Disposable | No |
| CSV, JSONL, and Parquet exports | Rebuildable study artifact | No |
| Generated reports | User output | No |

## Known constraints

- Downloading remains subject to YouTube availability, rate limits, and
  platform rules.
- Whisper transcription is CPU-heavy and is intentionally serial by default.
- One narrator or channel can reveal patterns but cannot independently
  corroborate them.
- Machine labels require sampled human review.
- Retrieval evaluation measures expected coverage, not ultimate truth.
- The company sample report is behind the current evidence contract.

## Approved next sequence

1. Phase 1: repair and validate the company sample report.
2. Phase 2: review topical labels and add query scope.
3. Phase 3: create case cards, causal chains, pattern matrices, teaching notes,
   and pedagogic evaluations.
4. Phase 4: add source-backed synthesis and a second-source pilot.
5. Phase 5: capture positions 21–35, review, then continue in gated batches.
6. Phase 6: improve portable archives and notebook surfaces.
7. Phase 7: extend the proven workflow into domain intelligence.

See `ROADMAP.md` for acceptance gates and
`docs/topical-intelligence/scale-and-learning-plan.md` for the batching,
relabeling, and pedagogic design.
