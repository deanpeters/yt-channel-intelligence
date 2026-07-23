# Topical Corpus Scale and Learning Plan

**Status:** Queue, first calibration batch, exports, and notebook implemented

**Working corpus:** Business failures

**Playlist inventory:** 121 videos as checked on 2026-07-23
**Current checkpoint:** 20 captured, 101 queued but not yet captured

## Recommendation

Do not treat the remaining playlist as one 101-video job. Grow the corpus through
review gates:

| Stage | Corpus size | Purpose | Gate before continuing |
|---|---:|---|---|
| Learning set | 10 | Stress the first taxonomy and retrieval design | Review cases, sponsor boundaries, label gaps, and fixed evaluation |
| Calibration batch | 20 | Test whether revised retrieval and taxonomy generalize | Complete: no unlabeled content or sponsor leakage; retrieval still needs scope |
| Expansion batches | +15 to +20 | Capture breadth without creating an unreviewable backlog | Batch report reviewed and taxonomy drift decision recorded |
| Full corpus | 121 | Complete the source collection | All queue items terminal; exports and index reproducible |

The ten-video checkpoint showed why this matters. Increasing the index from 62
to 193 content passages reduced strict retrieval from 7/10 to 4/10 and complete
case coverage from 10/10 to 7/10 on the unchanged evaluation. More data did not
automatically produce better retrieval.

The twenty-video checkpoint reinforced the finding. The unchanged questions,
which were written for the first three cases and do not name them, score 5/10
strict and 5/10 complete case coverage. A separate suite covering the expanded
case roles and mechanisms scores 8/10 on both measures. The next retrieval
improvement should add explicit case scope or conversational context, not tune
the old expected answers into a generic query.

## Implemented checkpoint

The current implementation now provides:

- a materialized 121-item SQLite queue with capture boundaries;
- append-only download and transcription attempts;
- worker identifiers, retry timing, stale-claim recovery, and error state;
- two paced download workers and one serialized local Whisper worker;
- taxonomy-version-aware relabeling and disposable collection versions;
- hybrid semantic, mechanism, causal-role, and case-role retrieval;
- CSV, JSONL, and Parquet exports;
- a starter local/Google Colab notebook;
- separate immutable regression and calibration evaluation suites.

## Durable queue and resume state

SQLite should remain the source of truth. Before bulk capture, discovery should
materialize all playlist entries into a stable queue rather than rediscovering
the next range on every run.

Each queue record should retain:

- `video_id`, `playlist_id`, and immutable `playlist_index_at_discovery`
- title, source URL, publication date, duration, and discovery timestamp
- state: `planned`, `downloading`, `downloaded`, `transcribing`,
  `transcribed`, `enriching`, `enriched`, `indexed`, `failed`, or `deferred`
- attempt count, last error, last transition time, and next eligible retry
- worker/run identifier and heartbeat for detecting abandoned work
- audio, subtitle, canonical transcript, and enrichment paths
- source checksum or size where useful
- transcript model and taxonomy version

Add an append-only `capture_attempts` table for run history instead of
overwriting the only error record. A worker should claim one row in a short
transaction, perform slow work outside the transaction, then write the result.
If a process dies, a stale heartbeat makes the item eligible for retry.

All file paths should be deterministic by `video_id`. A retry should discover
and reuse a valid completed artifact rather than create a duplicate. The current
`channel.db` status and per-video folders are the foundation of this design, but
they do not yet provide worker claims, heartbeats, or attempt history.

## Batches, pauses, and retries

Use two separate work queues:

1. **Capture queue:** metadata, subtitle, and audio downloads.
2. **Compute queue:** transcription, enrichment, and embedding.

Recommended starting defaults:

- one playlist metadata pass per batch, not one full playlist scan per video
- two download workers, increased to three only after a clean trial
- randomized 3–8 second delay between video downloads
- 1–2 seconds between lightweight metadata/subtitle requests
- exponential backoff with jitter after HTTP 403, 429, or transient network
  failures; do not immediately fan out more workers
- checkpoint after every video and stop cleanly after the requested batch size

These values are conservative starting points, not a claim about a YouTube
rate-limit threshold. Make them configuration values and record the effective
settings with each run. yt-dlp already provides
[`--sleep-requests`, `--sleep-interval`, `--max-sleep-interval`, and
`--sleep-subtitles`](https://github.com/yt-dlp/yt-dlp#workarounds), so the
capture layer should expose those controls rather than invent its own hidden
timers.

Retry only failed states. Use capped exponential backoff, and move repeated
failures to `deferred` for human review rather than blocking the rest of a
batch.

## Parallel work: processes before agents

Bulk media capture is better handled by a small worker pool than by multiple
browser or coding-agent tasks.

- Downloads are I/O-bound: start with two concurrent workers.
- Local Whisper is memory- and compute-bound: use one `small.en` worker on this
  machine until a benchmark proves that two are faster and stable.
- Embedding can batch many passages in one local process.
- Database writes should be short and transactional; workers should not keep
  SQLite connections open across long media operations.

Browser agents add page-rendering overhead and make resume state harder to
coordinate. They are useful for a manual exception—a consent page, a disputed
caption, or source inspection—not the normal download path.

Multiple coding agents can help with independent human-review work, such as
reviewing disjoint case packets or proposing taxonomy changes. They should not
all mutate the same SQLite database or Chroma collection. If parallel agent
capture is ever tested, give each worker a disjoint manifest range and separate
workspace/database shard, then merge through a deterministic import step.

## Taxonomy, relabeling, and reindexing

Treat these as separate layers:

```text
immutable source -> canonical transcript -> versioned enrichment -> disposable index
```

Changing the taxonomy should never require another download or transcription.
The current enrichment command now reuses labels only when their
`taxonomy_version` matches. A version change makes passages eligible for
relabeling; `--relabel-all` supports an explicit refresh within one version.

At each batch checkpoint:

1. Sample every new case at the case level.
2. Review sponsor boundaries and a stratified set of passages: high-confidence,
   ambiguous, unlabeled, and novel.
3. Produce a drift note containing proposed new labels, overloaded labels,
   labels never used, and recurring passages that do not fit.
4. Decide whether to keep the taxonomy or bump its version.
5. Relabel only affected passages when the meaning is unchanged; relabel the
   corpus when label meanings or boundaries change.
6. Build a new collection name instead of editing the active collection in
   place.
7. Run the fixed regression questions plus new questions justified by new
   cases.
8. Promote the new index only after review.

Evaluation questions are evidence, not a target to game. Keep an immutable core
suite and add versioned expansion suites. Report case coverage, mechanism
coverage, sponsor leakage, source diversity, and unsupported synthesis
separately.

## Turning transcripts into pedagogic material

Retrieval is an ingredient, not the learning product. Add a derived learning
layer with four artifacts:

1. **Case cards:** initial advantage, pivotal decisions, warning signs,
   mechanisms, visible outcomes, attempted responses, and source links.
2. **Causal chains:** ordered claims in the form `condition -> decision ->
   mechanism -> consequence`, with every link marked source claim or analyst
   inference.
3. **Cross-case pattern matrix:** cases as rows and mechanisms as columns,
   with timestamped evidence in populated cells.
4. **Teaching notes:** lesson, why it matters, boundary conditions,
   counterexample, discussion question, and what additional evidence would
   change the lesson.

Patterns should graduate through named levels:

- **Observation:** present in one passage.
- **Case pattern:** repeated within one case.
- **Cross-case pattern:** present in multiple distinct cases.
- **Corroborated lesson:** supported beyond this one narrator or channel.

This prevents a compelling anecdote from silently becoming a general rule.

## Notebook and portable-data path

Chroma should not be the only way to study the corpus. Add deterministic exports
generated from `corpus.json` and `passages.jsonl`:

- `cases.csv` for simple inspection
- `passages.jsonl` as the lossless interchange format
- `passages.parquet` for efficient analysis with pandas, Polars, or DuckDB
- `case_mechanisms.csv` as a tidy many-to-many table
- canonical Markdown transcripts for reading and Obsidian-style use

A starter notebook should load the exports, not reach into the live SQLite or
Chroma internals. Suggested sections:

1. corpus inventory and completeness
2. cases by industry, subject type, and failure state
3. label frequency and co-occurrence
4. sponsor and transcript-quality audit
5. cross-case mechanism matrix
6. passage sampling for human review
7. candidate teaching themes and counterexamples

For Google Colab, publish a data-only archive containing the manifest, canonical
transcripts, JSONL/CSV/Parquet exports, taxonomy config, and notebook. Exclude
audio and the generated Chroma directory by default; both are large and the
index is rebuildable. The notebook should accept either an uploaded archive or
a mounted Google Drive folder and should run without private API keys for
exploratory analysis.

## Next implementation slice

Before videos 21–35:

1. add explicit case-set, industry, case-role, or playlist-range query scope;
2. review the notebook's stratified v0.3 passage sample and record corrections;
3. generate source-linked case cards and causal chains for all twenty cases;
4. add pedagogic evaluation questions for patterns, counterexamples, and
   boundary conditions;
5. capture positions 21–35 only if the scoped retrieval and learning artifacts
   pass review.
