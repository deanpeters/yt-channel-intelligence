# AGENTS.md — Channel Intelligence

## Start here

Read these files before changing the project:

1. `README.md` — user-facing purpose, setup, and workflows
2. `docs/current-state.md` — implemented state, evidence, and restart point
3. `ROADMAP.md` — approved execution phases
4. `CLAUDE.md` — architecture, product principles, and implementation rules
5. The relevant topical design docs under `docs/topical-intelligence/`

Treat the live code and tests as the source of truth when older prose conflicts.
Update `docs/current-state.md` after a meaningful architecture or workflow
change so another agent can resume cold.

## Product purpose

This repository turns public long-form media into traceable intelligence.

It currently has two modes:

- **Company intelligence:** analyze a company's recent YouTube material and
  produce a structured, evidence-backed report.
- **Topical intelligence:** capture a bounded playlist, preserve transcripts,
  apply versioned labels, retrieve source passages, and create portable study
  data for learning across cases.

Topical intelligence is the foundation for a later multi-source domain
intelligence mode. Do not collapse the company report pipeline into the topical
retrieval pipeline; they share capture infrastructure but serve different jobs.

## Product and engineering rules

- Optimize for useful, attributable insight—not pipeline theater.
- Preserve raw source material separately from generated labels and analysis.
- Every derived claim must retain video, timestamp, and transcript provenance.
- Sponsor passages must never enter the retrieval index.
- Taxonomy changes trigger relabeling or reindexing, not another download.
- Generated Chroma indexes are disposable; canonical transcripts and
  enrichment records are durable.
- Keep secrets in environment variables. Never commit keys, `.env` files,
  audio, transcripts, local databases, generated indexes, or reports.
- Prefer plain files, SQLite, Markdown, JSONL, CSV, and Parquet over unnecessary
  services.
- Keep beginner-facing setup and errors understandable to Product Managers and
  other capable non-specialists.

## Current topical checkpoint

The business-failures corpus currently contains (as of positions 1–50; batches
continue toward the full 121-entry playlist):

- 121 playlist entries in the durable queue; 50 captured and transcribed
- taxonomy `0.3-workup`, 31 curated `passage_overrides`
- 919 labeled passages, 106 sponsor passages excluded, 813 in Chroma
- 0 unlabeled passages
- fixed retrieval regression 5/10, calibration 8/10 (stable across corpus growth)
- 4/50 cases corroborated against an independent source

Phases 2, 3, 4, 6 are complete; Phase 5 is in progress (the reviewed-batch loop
is proven); Phase 7 has started (corpus-wide corroboration and a data-driven
naming gate; cross-channel ingestion still to do). See `docs/current-state.md`
for the authoritative phase status and command reference.

## Two environments

Topical work uses two virtual environments. If a command touches YouTube or
Whisper it runs in `.venv-capture` (built by `setup-capture.sh`); everything in
`topic_corpus.py` runs in `.venv-topic` (built by `setup-topic.sh`).

To grow the corpus, use the two-step batch loop:

```bash
bash batch-1-capture.sh "<playlist-url>" <up-to-position>   # capture + draft
# review reports/topics/<slug>-draft-cases.yaml, paste into topics/<slug>.yaml
bash batch-2-build.sh                                        # enrich..evals
```

## Useful verification commands

For any code or architecture change:

```bash
python3 -m compileall -q agent.py db.py phases topic_corpus.py
python3 -m unittest discover -s tests -v
git diff --check
```

For topical changes, also rebuild the affected derived layer and run both
retrieval suites plus the pedagogic evaluation when the local corpus is present:

```bash
.venv-topic/bin/python topic_corpus.py enrich --label-with-llm
.venv-topic/bin/python topic_corpus.py index
.venv-topic/bin/python topic_corpus.py learn
.venv-topic/bin/python topic_corpus.py teach
.venv-topic/bin/python topic_corpus.py evaluate
.venv-topic/bin/python topic_corpus.py evaluate \
  --questions evaluations/business-failures-calibration-questions.yaml \
  --output reports/topics/business-failures-calibration-evaluation.md
.venv-topic/bin/python topic_corpus.py evaluate-learning
```

The local corpus lives under `.workspace/` and is intentionally uncommitted.
Commands requiring it should fail gracefully when run from a clean clone.
