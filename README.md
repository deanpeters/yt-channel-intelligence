# Channel Intelligence

Point it at a company's YouTube channel. Come back with a structured competitive intelligence report — built from what that company has actually said, in their own words, over the past two and a half years.

Designed for product managers, coaches, and trainers who need to understand a competitor or partner before a meeting, not after.

---

## Current project state

The original company-intelligence report workflow remains intact. An
experimental topical-intelligence workflow now captures a bounded playlist,
creates versioned transcript enrichment, builds a source-linked retrieval
index, and exports portable study data.

The current business-failures calibration checkpoint contains 20 transcribed
cases from a 121-video playlist queue, 388 labeled passages, 54 excluded sponsor
passages, and 334 searchable passages. The next work is review and learning
design—not another capture batch.

For an evidence-backed implementation inventory and cold-start handoff, read
[`docs/current-state.md`](docs/current-state.md). Contributors and coding agents
should begin with [`AGENTS.md`](AGENTS.md), then use
[`ROADMAP.md`](ROADMAP.md) for the approved phase sequence.

---

## What you get

A report with ten sections, each backed by verbatim quotes from the source videos:

| Section | What it answers |
|---|---|
| **Executive summary** | The strategic picture in four sentences — what they're trying to do that they haven't fully said out loud |
| **Product line** | Every product mentioned, how many videos it appears in, and what its presence signals |
| **The problem they're obsessed with** | The customer pain driving everything they build |
| **Who they're building for** | The mindset and job-to-be-done — and who they're deliberately *not* building for |
| **How they decide what to build** | The principle behind their product decisions, including what they refuse to do |
| **Where they're placing bets** | What they're investing in, and what has to be true for that bet to pay off |
| **How they frame the category** | Are they creating a new space, or reframing to escape a comparison? |
| **Momentum and tone** | On offense or defense? Confident or hedging? Accelerating or consolidating? |
| **What's shifted** | How their messaging has changed — what disappeared, what's new |
| **What they're not saying** | Conspicuous gaps and what the silence reveals |

Every claim is anchored to a verbatim quote and the video it came from. The "What they're not saying" section is the exception — it's analytical inference about absence, and it's labeled as such.

---

## What you need

- A Mac or Windows PC
- An API key for your AI provider — the tool uses an LLM to read transcripts and generate your report. It defaults to OpenAI's `gpt-4o-mini`, but also works with Anthropic, Google Gemini, or a local model via [Ollama](https://ollama.com) (no key required). See the [Setup Guide](SETUP.md) for all options.
- About 30–90 minutes for a first run (mostly unattended — the tool does the work)

That's it. The setup script installs everything else.

> **New here?** See the full [Setup Guide](SETUP.md) for step-by-step instructions including how to get an API key, what it costs, and how to troubleshoot common issues.

---

## Setup (do this once)

### Step 1 — Download this tool

Download the project folder and unzip it somewhere you'll remember (your Desktop is fine).

### Step 2 — Open a terminal

**Mac:** Press `Command + Space`, type `Terminal`, press Enter.

**Windows:** Press the Windows key, type `cmd`, press Enter.

In the terminal, navigate to the folder you just downloaded. If you put it on your Desktop:

**Mac:**
```
cd ~/Desktop/yt-channel-intelligence
```

**Windows:**
```
cd %USERPROFILE%\Desktop\yt-channel-intelligence
```

### Step 3 — Run the setup script

**Mac:**
```
bash setup.sh
```

**Windows:**
```
setup.bat
```

The setup script checks your system, installs the tools this project needs, and tells you exactly what to do at each step. If anything is missing, it explains what to install and how. Run it again after fixing anything it flags — it will confirm everything is in order.

### Step 4 — Add your OpenAI API key

If you don't have an OpenAI API key yet, get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). You'll need to create a free account if you don't have one.

The setup script will tell you how to save your key so you don't have to enter it every time.

---

## Running it

Once setup is done, run the tool with any public YouTube channel URL. All of these formats work:

```
# A channel's video tab (most common)
python3 agent.py https://www.youtube.com/@CompanyName/videos

# The channel root — same result as /videos
python3 agent.py https://www.youtube.com/@CompanyName

# A courses tab
python3 agent.py https://www.youtube.com/@CompanyName/courses

# A specific playlist
python3 agent.py https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxx
```

On Windows, use `python` instead of `python3`.

Each URL produces a separate report and workspace, so you can run multiple channels without them interfering with each other.

You'll see progress as it works:

```
Discovering videos since December 2023...
Found 50 videos (capped), 12 shorts skipped.
Downloading audio for 50 video(s)...
  Downloaded 1/50: What Great PMs Actually Do
  Downloaded 2/50: The Discovery Mistake Most Teams Make
  ...
Transcribing 50 video(s)...
  ...
Analyzing 50 video(s)...
  ...
Synthesizing report from 50 video(s)...

Report ready: reports/productside-2026-06-30.md
```

When it's done, it prints exactly one line telling you where your report is.

---

## Your reports

All reports land in the `reports/` folder inside the project, named by company and date:

```
reports/
├── productside-2026-06-29.md
├── anothercompany-2026-07-01.md
└── ...
```

Open the `.md` file in:
- **Notion** — paste the file contents or import directly
- **VS Code** — right-click → Open Preview for a formatted view
- **Any text editor** — it's plain text and readable as-is

---

## Running it again or resuming

If a run is interrupted, or you want to refresh a report, just run the same command again. The tool picks up exactly where it left off — videos already downloaded or transcribed won't be re-processed. Only the work that wasn't finished will run.

---

## Running multiple companies

Each company is tracked separately. Run the tool with a different URL and it creates a new workspace and report without touching anything from previous runs.

```
python3 agent.py https://www.youtube.com/@CompanyA/videos
python3 agent.py https://www.youtube.com/@CompanyB/videos
python3 agent.py https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxx
```

---

## Experimental: capture a topical corpus

Topical mode captures source material for a knowledge base without applying the company-intelligence report questions to it.

### Adding a batch of videos — two steps

To grow the corpus you run two scripts with one manual review in between. They
handle the environments for you.

```bash
# STEP 1 — capture the videos and draft their case configs.
# The last number is the playlist position to capture up to.
bash batch-1-capture.sh "https://www.youtube.com/playlist?list=PLZ6vahBdAJ3iArMOb5Mrpav98SjW9dsaz" 50
```

Step 1 prints the one file to review. Open it, check the case roles and sponsor
timestamps, and paste its entries into the `cases:` block of
`topics/business-failures.yaml`. Then:

```bash
# STEP 2 — label, index, rebuild the learning layer, and confirm nothing broke.
bash batch-2-build.sh
```

That is the whole loop: **capture → review one file → build.** Step 1 is safe to
re-run and resumes where it left off. Everything else in this section is the
lower-level detail behind those two scripts.

Under the hood the capture step runs the same pipeline directly:

```bash
python3 agent.py \
  --mode topic \
  --topic "Business failures" \
  --limit 20 \
  --whisper-model small.en \
  "https://www.youtube.com/playlist?list=PLZ6vahBdAJ3iArMOb5Mrpav98SjW9dsaz"
```

This creates resumable audio, raw transcripts, timestamped subtitles, canonical Markdown transcripts, and a corpus manifest under `.workspace/topics/business-failures/`. Running the same command again skips completed downloads and transcriptions.

When you capture a new batch (for example raising `--limit` to pull the next
playlist positions), each new video needs a reviewed `cases:` entry before it
can be enriched. Draft those entries from the fresh transcripts, then review
and paste them into the topic config:

```bash
.venv-topic/bin/python topic_corpus.py draft-cases
```

`draft-cases` proposes a subject, case role, failure mechanisms, and sponsor
intervals for every captured video that has no case yet, writing a YAML snippet
to `reports/topics/`. It is a draft to correct, not an automatic commit into the
taxonomy — always check the case roles and sponsor timestamps before pasting.

Enrich the transcripts with the reviewed taxonomy, build the disposable local
index, create portable study files, and try a question. Enrichment also
writes a `<SUBJECT>.md` marker next to each `transcript.md` (e.g.
`PIZZA_HUT.md`) and a top-level `INDEX.md` in the workspace, so you can browse
the video-ID folders by company instead of opening each one:

```bash
bash setup-topic.sh
.venv-topic/bin/python topic_corpus.py enrich --label-with-llm
.venv-topic/bin/python topic_corpus.py index
.venv-topic/bin/python topic_corpus.py export
.venv-topic/bin/python topic_corpus.py query "How did short-term incentives undermine long-term health?"
```

Scope a query to part of the corpus — by industry, case role, specific case
(video ID or subject substring), or playlist range — to focus retrieval:

```bash
# Only restaurants, only the first fourteen playlist positions
.venv-topic/bin/python topic_corpus.py query \
  "How did cost structure and value perception drive decline?" \
  --industry restaurants --playlist-max 14

# Only the counterexamples
.venv-topic/bin/python topic_corpus.py query \
  "How did the company recover or adapt?" \
  --case-role turnaround_counterexample --case-role resilience_counterexample

# A single case by subject substring
.venv-topic/bin/python topic_corpus.py query "Why did growth stall?" --case snapchat
```

Audit the machine-applied labels. Draw a reproducible stratified sample into a
review worksheet, mark corrections in the `verdict` / `add_` / `remove_` /
`set_epistemic_status` / `note` columns (in the notebook, a spreadsheet, or any
CSV editor), then convert your markup into a `passage_overrides` snippet:

```bash
.venv-topic/bin/python topic_corpus.py review-sample --per-stratum 2 --stratify-by case
# ...fill in the worksheet...
.venv-topic/bin/python topic_corpus.py review-apply \
  reports/topics/business-failures-label-review.csv
```

`review-apply` prints a review summary (reviewed / confirmed / corrected /
error rate) to help decide whether the taxonomy needs a version bump. Paste the
snippet's entries into `passage_overrides` in the topic config, then re-run
`enrich` and `index`.

Run the ten-question retrieval check:

```bash
.venv-topic/bin/python topic_corpus.py evaluate
```

Run the twenty-video calibration check:

```bash
.venv-topic/bin/python topic_corpus.py evaluate \
  --questions evaluations/business-failures-calibration-questions.yaml \
  --output reports/topics/business-failures-calibration-evaluation.md
```

Build the deterministic learning layer — source-linked case cards, causal
chains, and a cross-case pattern matrix aggregated from the reviewed labels
(no LLM calls):

```bash
.venv-topic/bin/python topic_corpus.py learn
```

This writes per-case Markdown cards, `case-cards.json`, and
`pattern-matrix.csv` under `.workspace/topics/business-failures/learning/`.
Each card links every mechanism and causal-chain node to its source passage
and timestamp, and flags evidence gaps (mechanisms asserted for a case but
never backed by a direct source claim).

Add the LLM prose layer — teaching notes written on top of the case cards.
Every lesson cites a timestamp that exists in the card, is tagged
source-supported or analyst-inference, and each case's evidence gaps become an
explicit "cannot yet claim" section. Citations are validated against the card,
so a hallucinated timestamp is flagged rather than trusted:

```bash
.venv-topic/bin/python topic_corpus.py teach
```

This writes per-case teaching notes (Markdown + JSON) under
`.workspace/topics/business-failures/learning/teaching-notes/` and reports how
many lessons, if any, failed citation validation.

Run the pedagogic evaluation — mechanical checks over the learning layer
(citation integrity, counterexample coverage, boundary conditions, evidence-gap
disclosure, and within-corpus pattern recurrence with single-case mechanisms
flagged provisional):

```bash
.venv-topic/bin/python topic_corpus.py evaluate-learning
```

Synthesize a source-backed answer. Retrieval (optionally scoped) selects the
passages; the answer cites them by evidence tag, marks each claim
source-supported or analyst-inference, and puts anything the evidence does not
establish into a limitations section. Citations are validated against the
retrieved passages:

```bash
.venv-topic/bin/python topic_corpus.py answer \
  "What warning signs appeared before these businesses declined?"
```

Corroborate one case against an independent second source. Provide a reference
file of publicly-sourced facts under `corroboration/<corpus>/<video-id>.yaml`;
the check labels each corpus mechanism corroborated, uncorroborated, or
contradicted, surfaces facts the corpus omits, and reports corroboration
coverage. Until coverage is broad, the corpus is a single-channel topical
corpus, not domain intelligence:

```bash
.venv-topic/bin/python topic_corpus.py corroborate FTX
```

The export command creates CSV, JSONL, and Parquet study files. Open
[`notebooks/business-failures-exploration.ipynb`](notebooks/business-failures-exploration.ipynb)
locally, in Google Colab, or in Google Antigravity to inspect cases, labels,
review samples, and candidate teaching themes.

For local Jupyter, run `bash setup-topic.sh`, open the notebook, and select
**YT Channel Intelligence (topic)** from the kernel picker. This keeps Jupyter
on the same Python environment that contains pandas, PyArrow, and the topical
retrieval dependencies.

This is currently a research spike, not a finished domain-truth engine. See
[Business Failures Topical Intelligence Spike](docs/topical-intelligence/business-failures-spike.md)
for the provisional taxonomy and measured retrieval results, and
[Topical Corpus Scale and Learning Plan](docs/topical-intelligence/scale-and-learning-plan.md)
for the proposed batching, queue, parallelism, relabeling, pedagogy, and
notebook path.

---

## What's coming

See [ROADMAP.md](ROADMAP.md) for planned improvements — incremental updates, parallel transcription, podcast/RSS ingestion, vector search, and company comparison mode.

---

## Limitations

- Only works with public YouTube channels
- Transcription quality depends on audio quality — if a speaker has a heavy accent or there's loud background noise, some quotes may be slightly off
- Non-English channels work but require changing `WHISPER_MODEL` to `large-v3` in `config.py` (significantly slower)
- The report reflects what the company has chosen to say on YouTube — it won't surface things they haven't discussed publicly

---

## How to use your report

Not sure what to do with the report once you have it? See [Using Your Report](USING-YOUR-REPORT.md) — a section-by-section guide to what each section tells you, what to look for, and how to use it before a meeting.

---

## If something goes wrong

**"Command not found" after setup:** Close the terminal, open a new one, and try again. Some tools need a fresh terminal window before they're recognized.

**The run stops partway through:** Run the same command again. It resumes from where it stopped.

**"OPENAI_API_KEY" error:** Your API key isn't set. Re-run the setup script and follow the instructions for adding it.

**A video was skipped:** Some videos are unavailable due to regional restrictions or removal after the channel was scanned. The report is built from all videos that completed successfully.
