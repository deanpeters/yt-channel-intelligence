# Setup Guide

This guide walks you through getting Channel Intelligence running for the first time. It takes about 15 minutes. Most of it is just waiting for things to install.

---

## Overview

There are four things to do before you can run your first report:

1. Download this tool
2. Get an OpenAI API key
3. Run the setup script
4. Run your first report

---

## Step 1 — Download this tool

Go to the GitHub repository and click the green **Code** button, then **Download ZIP**.

Unzip the file. Move the resulting folder (`yt-channel-intelligence`) somewhere you'll remember — your Desktop or Documents folder works well.

---

## Step 2 — Choose your AI provider and get an API key

The tool uses an LLM to read transcripts and write your report. You can choose which provider to use:

| Provider | Model | Cost per report | Key required |
|---|---|---|---|
| **OpenAI** (default) | `gpt-4o-mini` | ~$0.50–$3.00 | Yes — [platform.openai.com](https://platform.openai.com/api-keys) |
| **Anthropic** | `anthropic/claude-haiku-4-5` | ~$0.50–$2.00 | Yes — [console.anthropic.com](https://console.anthropic.com/) |
| **Google** | `gemini/gemini-1.5-flash` | ~$0.10–$1.00 | Yes — [aistudio.google.com](https://aistudio.google.com/apikey) |
| **Ollama** (local) | `ollama/llama3.2` | Free | No — runs on your machine |

Pick one and follow the instructions for it below. You only need one.

---

### Option A — OpenAI (default, no extra setup needed)

**2a. Create an account** at [platform.openai.com](https://platform.openai.com). You can sign up with Google or email.

**2b. Add a payment method** — Go to **Billing → Payment methods** and add a card. You're only charged for what you use.

**2c. Generate an API key** — In the left sidebar, click **API keys → Create new secret key**. Give it a name, click **Create**, and copy the key immediately — it starts with `sk-` and is only shown once.

**2d. Save the key:**

Mac:
```
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.zshrc && source ~/.zshrc
```

Windows — add `OPENAI_API_KEY` to your User variables in **System Properties → Environment Variables**.

---

### Option B — Anthropic

**2a.** Create an account at [console.anthropic.com](https://console.anthropic.com/) and add a payment method under **Billing**.

**2b.** Go to **API Keys → Create Key**, copy it (starts with `sk-ant-`).

**2c.** Save the key AND tell the tool to use Anthropic:

Mac:
```
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
echo 'export LLM_MODEL="anthropic/claude-haiku-4-5"' >> ~/.zshrc
source ~/.zshrc
```

Windows — add both `ANTHROPIC_API_KEY` and `LLM_MODEL` to your User variables.

---

### Option C — Google Gemini

**2a.** Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and click **Create API key**. Copy it.

**2b.** Save the key AND tell the tool to use Google:

Mac:
```
echo 'export GEMINI_API_KEY="AI..."' >> ~/.zshrc
echo 'export LLM_MODEL="gemini/gemini-1.5-flash"' >> ~/.zshrc
source ~/.zshrc
```

Windows — add both `GEMINI_API_KEY` and `LLM_MODEL` to your User variables.

---

### Option D — Ollama (local, free, no API key)

**2a.** Download and install Ollama from [ollama.com](https://ollama.com).

**2b.** Pull a model — in your terminal:
```
ollama pull llama3.2
```

**2c.** Tell the tool to use Ollama:

Mac:
```
echo 'export LLM_MODEL="ollama/llama3.2"' >> ~/.zshrc && source ~/.zshrc
```

Windows — add `LLM_MODEL` set to `ollama/llama3.2` to your User variables.

Make sure Ollama is running before you generate reports. Quality will vary by model — `llama3.2` is a reasonable starting point; larger models produce better results.

---

> **Confirm your key is set (Mac):** Open a new terminal and run `echo $OPENAI_API_KEY` (or the matching variable for your provider). You should see the key printed back.
>
> **Confirm your key is set (Windows):** Open a new Command Prompt and run `echo %OPENAI_API_KEY%` (or the matching variable).

---

## Step 3 — Run the setup script

The setup script checks your system and installs the remaining tools the project needs (yt-dlp for YouTube downloading, ffmpeg for audio processing, and Whisper for transcription). It tells you clearly if anything is missing and what to do about it.

**Open a terminal and navigate to the project folder.**

If you put the folder on your Desktop:

Mac:
```
cd ~/Desktop/yt-channel-intelligence
```

Windows:
```
cd %USERPROFILE%\Desktop\yt-channel-intelligence
```

**Run the setup script:**

Mac:
```
bash setup.sh
```

Windows:
```
setup.bat
```

Follow the instructions on screen. If everything passes, you'll see **All set! You're ready to go.**

If anything is flagged with a ✗ or [X], fix it and re-run the script. Each check will pass once the issue is resolved. The most common issues are:

- **Homebrew not installed (Mac):** The script gives you the install command. Copy it, run it, then re-run `bash setup.sh`.
- **OpenAI API key not found:** Go back to Step 2d and make sure you saved it correctly, then open a new terminal window and re-run.
- **ffmpeg not found (Windows):** The script tries to install it automatically. If that fails, it gives you manual download instructions.

---

## Step 4 — Run your first report

With setup complete, you're ready to go. Run the tool with any public YouTube channel URL:

**Mac:**
```
python3 agent.py https://www.youtube.com/@CompanyName/videos
```

**Windows:**
```
python agent.py https://www.youtube.com/@CompanyName/videos
```

Replace the URL with the channel you want to analyze. The tool will run through four phases automatically — discovering videos, downloading audio, transcribing, and generating the report. You'll see progress as it works.

When it's done:
```
Report ready: reports/companyname-2026-06-30.md
```

Open that file in a text editor, Notion, or VS Code. Your report is ready.

---

## What does it cost?

Each report costs roughly **$0.50 – $3.00** in OpenAI API usage, depending on the channel size and how many videos are analyzed. A 50-video channel typically runs under $2.

The tool uses `gpt-4o-mini`, which is one of OpenAI's most affordable models. You can monitor your usage at [platform.openai.com/usage](https://platform.openai.com/usage).

Transcription (the Whisper step) runs locally on your machine — it uses no API credits and has no additional cost.

---

## Running it again

Re-running the tool on the same channel is fast and cheap. Videos already transcribed are skipped. Only the AI synthesis (Pass 2) re-runs, which takes about 30 seconds and costs a few cents.

This means you can refresh a report at any time to pick up new videos the channel has published since your last run.

---

## Troubleshooting

**"python3: command not found" (Mac) or "python: command not found" (Windows)**
Python isn't installed or isn't on your PATH. Re-run the setup script — it will flag this and tell you what to install.

**"OPENAI_API_KEY" error when running the tool**
Your key isn't being found. Make sure you followed Step 2d, then open a fresh terminal window and try again.

**The run stops partway through**
Run the same command again. The tool resumes from where it stopped — nothing is lost.

**"yt-dlp version is older than 90 days" warning**
This is a warning, not an error. Some videos may be skipped. Update yt-dlp by running:
- Mac: `brew upgrade yt-dlp` or `pip3 install --upgrade yt-dlp`
- Windows: `pip install --upgrade yt-dlp`

**A video is skipped with no explanation**
Some videos are unavailable due to regional restrictions or having been removed after the channel was scanned. The report is built from all videos that completed successfully.

**Whisper is very slow**
Transcription speed depends on your machine. On an older Mac or PC, a 50-video channel may take 2–3 hours. The tool runs unattended — start it before a meeting or overnight. You can also switch to a faster (less accurate) model by changing `WHISPER_MODEL` to `small.en` or `base.en` in `config.py`.
