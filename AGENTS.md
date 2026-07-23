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

The business-failures calibration corpus currently contains:

- 121 playlist entries in the durable queue
- 20 captured and transcribed cases; 101 awaiting later batches
- taxonomy `0.3-workup`
- 388 labeled passages
- 54 sponsor passages excluded
- 334 passages in Chroma
- 0 unlabeled passages
- fixed retrieval regression: 5/10
- twenty-case calibration suite: 8/10

Do not capture videos 21–35 until the Phase 2 and Phase 3 learning gates in
`ROADMAP.md` are complete.

## Useful verification commands

```bash
python3 -m compileall -q agent.py db.py phases topic_corpus.py
python3 -m unittest discover -s tests -v
git diff --check
```

Topical checks:

```bash
bash setup-topic.sh
.venv-topic/bin/python topic_corpus.py enrich
.venv-topic/bin/python topic_corpus.py index
.venv-topic/bin/python topic_corpus.py export
.venv-topic/bin/python topic_corpus.py evaluate
.venv-topic/bin/python topic_corpus.py evaluate \
  --questions evaluations/business-failures-calibration-questions.yaml \
  --output reports/topics/business-failures-calibration-evaluation.md
```

The local corpus lives under `.workspace/` and is intentionally uncommitted.
Commands requiring it should fail gracefully when run from a clean clone.
