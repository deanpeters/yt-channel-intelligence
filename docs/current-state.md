# Current State and Restart Guide

**Checkpoint:** Phase 0 complete. Phase 2 complete: retrieval scoping and the
stratified label-review harness are implemented, a first-pass label audit
(stratified sample, seed 11) was run, and the taxonomy-bump decision is
resolved. The audit found the machine labeler's main weakness — negative
failure mechanisms applied to strength, rise, and counterexample passages —
and corrected nine egregious cases via `passage_overrides` (now 31 curated
overrides). The 27-mechanism vocabulary is adequate, so the taxonomy stays
`0.3-workup`; label errors are individual assignment fixes, not a vocabulary
change. Phase 3 complete:
the deterministic learning layer (case cards, causal chains, pattern matrix),
the citation-validated LLM teaching-notes prose layer, and the pedagogic
evaluation (all gating checks passing) are implemented. Phase 4 complete:
source-backed answer synthesis (`answer`) writes cited, inference-labeled
answers over scoped retrieval; a corroboration pilot (`corroborate`)
cross-checks one case (FTX) against an independent public-record second source
and enforces the naming gate. Phase 5 batches complete: playlist positions
21-80 were captured across reviewed batches, drafted into case configs with
`draft-cases`, reviewed, and integrated. The corpus is now 80 cases and 1249
indexed passages (149 sponsor passages excluded). Retrieval evals held stable
across the growth of the corpus (fixed regression 5/10, calibration 8/10),
and only one single-case mechanism (`adverse_selection`) remains provisional.
Phase 6 complete: `package` builds a portable, data-only archive (manifest,
canonical transcripts, taxonomy, enrichment, exports, learning artifacts,
evaluations, notebook) that excludes audio and the Chroma index and needs no
API key to open. Phase 7 started: corroboration now persists per-case results,
and `domain-status` aggregates them corpus-wide — coverage, claim outcomes, and
contradictions — with a data-driven naming gate. Four cases (FTX, WeWork,
Silicon Valley Bank, 23andMe) are corroborated against independent public-record
sources; at 4/80 coverage with open contradictions the gate correctly reports
the corpus is not yet domain intelligence. Full cross-channel domain
intelligence still requires ingesting a second source channel.

**Updated:** 2026-07-24

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

### Learning layer, synthesis, and corroboration

- `learn` aggregates the reviewed enrichment into deterministic, source-linked
  case cards, taxonomy-ordered causal chains, a cross-case pattern matrix, and
  evidence-gap detection (no LLM calls).
- `teach` writes LLM teaching notes on top of the cards; every lesson cites a
  card timestamp, is tagged source-supported or analyst-inference, and
  citations are validated after generation.
- `evaluate-learning` runs mechanical pedagogic checks (citation integrity,
  counterexample coverage, boundary conditions, evidence-gap disclosure,
  within-corpus pattern recurrence with single-case mechanisms flagged
  provisional).
- `answer` synthesizes a cited, inference-labeled answer over scoped retrieval.
- `corroborate` cross-checks a case against an independent public-record source;
  `domain-status` aggregates corroboration corpus-wide and gates the
  "domain intelligence" label on coverage and contradictions.

### Portable analysis

The `export` command creates `cases.csv`, `case_mechanisms.csv`,
`passages.csv`, `passages.jsonl`, `passages.parquet`, and `export-manifest.json`.
The `package` command bundles those plus canonical transcripts, taxonomy,
enrichment, learning artifacts, evaluations, and the notebook into a single
data-only zip under `dist/` (audio and the Chroma index excluded, no API key
needed).

The exploration notebook reads these exports rather than SQLite or Chroma. It
works locally with the registered **YT Channel Intelligence (topic)** kernel
and can be used in Google Colab or Google Antigravity by pointing it at the
export directory.

## Business-failures calibration evidence

Source playlist:

`https://www.youtube.com/playlist?list=PLZ6vahBdAJ3iArMOb5Mrpav98SjW9dsaz`

Current local checkpoint (as of the last committed batch — positions 1–80;
further batches continue the same loop):

| Measure | Result |
|---|---:|
| Playlist entries queued | 121 |
| Cases captured and transcribed | 80 |
| Cases awaiting later batches | 41 |
| Taxonomy | `0.3-workup` |
| Total passages | 1398 |
| Sponsor passages excluded | 149 |
| Indexed passages | 1249 |
| Unlabeled passages | 0 |
| Curated `passage_overrides` | 31 |
| Fixed regression score | 5/10 |
| Calibration score | 8/10 |
| Cases corroborated (independent source) | 4/80 |
| Sponsor leakage | 0 |

The fixed regression score has held at 5/10 as the corpus grew from 20 to 50
cases. It is deliberately not tuned to the larger corpus — it is a stable check
that growth has not broken the original three-case retrieval, not a target.
Query scope (`--industry`, `--case-role`, `--case`, `--playlist-min/max`) is the
supported way to narrow retrieval, rather than hidden tuning.

`case_role` distinguishes failures from counterexamples: Crocs is a turnaround
counterexample, Panda Express and Aldi are resilience counterexamples, American
Idol is a partial recovery. These must not be forced into failure labels merely
because they appear in the playlist.

## Two environments

Topical work uses two separate virtual environments. **Rule of thumb: if a
command touches YouTube or Whisper it runs in `.venv-capture`; everything else
runs in `.venv-topic`.**

| Env | Built by | Holds | Used for |
|---|---|---|---|
| `.venv-capture` | `setup-capture.sh` | yt-dlp, Whisper, litellm | download + transcribe (`agent.py`, `capture-topic.sh`) |
| `.venv-topic` | `setup-topic.sh` | chromadb, sentence-transformers, litellm, pandas, pyarrow | everything in `topic_corpus.py` |

## Growing the corpus (the reviewed-batch loop)

Two scripts with one manual review between them. `<N>` is the playlist position
to capture up to.

```bash
bash batch-1-capture.sh "<playlist-url>" <N>   # capture + draft case configs
# review reports/topics/<slug>-draft-cases.yaml, paste into topics/<slug>.yaml
bash batch-2-build.sh                          # enrich, index, learn, teach, evals
```

Watch for two things in the drafted configs before pasting: over-long sponsor
intervals (a sponsor read is ~30–90s; anything longer is likely wrong and would
exclude real content) and any `time_period` written as a bare integer.

## `topic_corpus.py` command reference

All run in `.venv-topic`; default `--config topics/business-failures.yaml`.

| Command | What it does | Phase |
|---|---|---|
| `draft-cases` | Draft a `cases:` entry per newly captured video (LLM) | 5 |
| `enrich [--label-with-llm]` | Chunk, sponsor-mark, and label passages into `passages.jsonl` | topical |
| `index` | Build the Chroma collection from indexable passages | topical |
| `query <q> [scope flags]` | Retrieve passages (scope by industry/case-role/case/playlist range) | 2 |
| `answer <q> [scope flags]` | Source-backed, inference-labeled synthesized answer | 4 |
| `review-sample` / `review-apply` | Stratified label-audit worksheet → `passage_overrides` | 2 |
| `learn` | Deterministic case cards, causal chains, pattern matrix | 3 |
| `teach` | LLM teaching notes over the cards (citation-validated) | 3 |
| `evaluate` / `evaluate --questions ...` | Fixed regression / calibration retrieval suites | topical |
| `evaluate-learning` | Pedagogic checks over the learning layer | 3 |
| `corroborate <case>` | Cross-check one case vs an independent source file | 4 |
| `domain-status` | Aggregate corroboration corpus-wide; data-driven naming gate | 7 |
| `export` | CSV / JSONL / Parquet study files | topical |
| `package` | Portable, data-only, API-key-free zip archive | 6 |

Rebuild the derived layers from scratch without re-downloading:

```bash
.venv-topic/bin/python topic_corpus.py enrich --label-with-llm
.venv-topic/bin/python topic_corpus.py index
.venv-topic/bin/python topic_corpus.py learn
.venv-topic/bin/python topic_corpus.py teach
.venv-topic/bin/python topic_corpus.py evaluate
.venv-topic/bin/python topic_corpus.py evaluate-learning
```

Corroboration references live in `corroboration/<slug>/<video-id>.yaml`
(committed, public-fact sources). Per-case corroboration results and the domain
status report are rebuildable local artifacts.

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

## Phase status

| Phase | Status |
|---|---|
| 0 — Document and checkpoint | Complete |
| 1 — Repair company sample report | Not started (independent track) |
| 2 — Review labels and add query scope | Complete |
| 3 — Learning layer (cards, chains, matrix, teaching, pedagogic evals) | Complete |
| 4 — Source-backed synthesis and corroboration pilot | Complete |
| 5 — Expand through reviewed batches | In progress (50/121 captured; loop proven) |
| 6 — Portable study surfaces | Complete |
| 7 — Domain intelligence | Started (corpus-wide corroboration + gate; cross-channel ingestion still to do) |

## What a new maintainer should pick up next

- **Finish Phase 5:** run the two-script batch loop for the remaining playlist
  positions (71 videos, ~5 batches). Each batch keeps the fixed regression at
  5/10 and needs a review of the drafted case configs before pasting.
- **Advance Phase 7:** add corroboration references for more cases to raise
  coverage, resolve or annotate the contradictions `domain-status` surfaces,
  and — the real frontier — ingest a second source channel so corroboration is
  genuinely cross-channel rather than corpus-vs-public-record.
- **Phase 1 (independent):** repair the company sample report to the evidence
  contract.

See `ROADMAP.md` for acceptance gates and
`docs/topical-intelligence/scale-and-learning-plan.md` for the batching,
relabeling, and pedagogic design.
