# CLAUDE.md — Channel Intelligence

## Product purpose

Channel Intelligence turns public long-form media into attributable
intelligence for Product Managers, product leaders, consultants, trainers, and
analysts.

It has two implemented modes:

1. **Company intelligence** produces a structured competitive-intelligence
   report from a company's recent YouTube material.
2. **Topical intelligence** turns a bounded playlist into a versioned,
   searchable, portable learning corpus.

Topical intelligence is the foundation for a later multi-source domain
intelligence mode. Read `docs/current-state.md` for the live checkpoint and
`ROADMAP.md` for the approved phase sequence.

## Outcome focus

**The end game is useful, traceable insight. All technical decisions serve that
outcome—not the other way around.**

Before adding complexity, ask:

- Does this make the resulting intelligence better, faster to obtain, easier
  to inspect, or safer to trust?
- Does it preserve context and provenance?
- Can a capable non-specialist run and understand it?
- Can another agent resume the work without reconstructing hidden decisions?

## Architecture boundary

The two modes share source capture but remain separate products:

```text
                         +-> company analysis -> canvas -> report
discover -> download -> transcribe
                         +-> canonical corpus -> enrichment -> index -> study
```

Do not replace the company report pipeline with retrieval. Do not force topical
cases into company-oriented report fields. Share the capture infrastructure and
source metadata; keep downstream analysis purpose-built.

## Design principles

- Reports and notebooks are user surfaces; `.workspace/` is operational state.
- CLI progress should be plain English, not internal log noise.
- Raw source text is immutable.
- Generated labels, causal roles, and interpretations live in a versioned
  enrichment layer.
- Every passage retains video ID, title, date, URL, and timestamps.
- Sponsor passages never enter the retrieval index.
- Chroma is disposable and rebuildable.
- Taxonomy changes should require relabeling or reindexing, never redownloading.
- Evaluation suites are evidence, not targets to game.
- One-channel patterns are provisional until corroborated elsewhere.
- Secrets come only from environment variables.

## Repository map

```text
yt-channel-intelligence/
├── AGENTS.md                     # agent start-here and verification contract
├── CLAUDE.md                     # architecture and implementation guidance
├── README.md                     # user-facing setup and workflows
├── ROADMAP.md                    # approved phases and feature horizons
├── SETUP.md                      # company-mode setup
├── USING-YOUR-REPORT.md          # company-report usage guide
├── docs/
│   ├── current-state.md          # restart-ready implementation checkpoint
│   └── topical-intelligence/
│       ├── business-failures-spike.md
│       └── scale-and-learning-plan.md
├── evaluations/                  # fixed and expansion retrieval suites
├── notebooks/                    # portable topical-analysis notebook
├── topics/                       # versioned taxonomy configuration
├── tests/                        # queue and retrieval-intent tests
├── agent.py                      # capture CLI for company and topic modes
├── topic_corpus.py               # topical enrichment/index/query/export CLI
├── db.py                         # queue, state, retries, and attempt history
├── phases/
│   ├── discover.py
│   ├── download.py
│   ├── transcribe.py
│   ├── synthesize.py
│   ├── topic.py
│   ├── topic_enrich.py
│   ├── topic_export.py
│   └── topic_retrieval.py
├── setup.sh / setup.bat          # company workflow setup
├── setup-topic.sh                # isolated topical environment and kernel
├── requirements-topic.txt
├── reports/                      # ignored generated output
└── .workspace/                   # ignored local corpus and operational state
```

## Company-intelligence workflow

1. Discover recent substantive videos using a rolling lookback.
2. Download audio.
3. Transcribe with Whisper.
4. Analyze each video into structured signals through LiteLLM.
5. Synthesize the signals into a cross-video canvas.
6. Render a Markdown report.

The report contract requires attributable evidence for factual claims.
`not_saying` is the explicit inference-about-absence exception. The current
sample report predates the strongest form of this contract and is scheduled for
repair in Phase 1.

## Topical-intelligence workflow

1. Materialize playlist metadata into the durable SQLite queue.
2. Apply a capture boundary such as `--limit 20`.
3. Download with a small, configurable worker pool and randomized delays.
4. Transcribe serially by default.
5. Build canonical Markdown transcripts and a corpus manifest.
6. Apply sponsor detection plus case- and passage-level labels.
7. Build a separate Chroma collection for each taxonomy version.
8. Query with hybrid semantic and taxonomy-aware ranking.
9. Run fixed and expansion evaluations.
10. Export CSV, JSONL, and Parquet for notebooks and other analysis tools.

## Queue and state

The SQLite video state machine supports:

```text
discovered
  -> downloading -> downloaded
  -> transcribing -> transcribed

download_failed / transcription_failed
  -> retry after next_retry_at
```

`capture_attempts` is append-only history. Video records retain transition
times, errors, worker IDs, heartbeats, and retry timing. Discovery refreshes
must not reset completed states.

Company analysis continues from `transcribed` to `analyzed`.

## Topical data model

Keep these layers separate:

```text
immutable source
  -> canonical transcript
  -> versioned enrichment
  -> disposable retrieval index
  -> derived learning artifacts
```

The business-failures taxonomy is currently `0.3-workup`. It includes failure
mechanisms, causal roles, passage labels, sponsor boundaries, and `case_role`
values that distinguish failures from turnaround and resilience
counterexamples.

## Local environments

Company mode uses the main Python/system setup described in `SETUP.md`.

Topical retrieval uses `.venv-topic`:

```bash
bash setup-topic.sh
```

The setup also registers the Jupyter kernel:

```text
YT Channel Intelligence (topic)
```

Use that kernel locally. The notebook can also read exported data in Google
Colab or Google Antigravity.

## LLM provider

LiteLLM provides the provider-neutral interface. `LLM_MODEL` selects the model;
provider credentials remain environment variables. Do not add per-provider
branches unless LiteLLM cannot support a required behavior.

## Security and repository hygiene

Never commit:

- API keys, tokens, credentials, or `.env` files
- `.workspace/`
- raw audio or transcripts
- SQLite databases
- Chroma indexes
- generated reports
- `.venv-topic/`

This repository is public. Treat every staged file as publishable material:
verify ignored local data, scan for credentials, and review the staged diff
before pushing.

## Required verification

For code or architecture changes:

```bash
python3 -m compileall -q agent.py db.py phases topic_corpus.py
python3 -m unittest discover -s tests -v
git diff --check
```

For topical changes, also rebuild the relevant derived layer and run both
retrieval suites when the local corpus is available.

Update `docs/current-state.md` after a meaningful change. Report validation
results honestly; do not hide regressions caused by corpus growth.
