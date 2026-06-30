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

## Step 2 — Get an OpenAI API key

The tool uses OpenAI's AI to read the video transcripts and write your report. You need an API key to use it. This takes about five minutes.

### 2a. Create an OpenAI account

Go to [platform.openai.com](https://platform.openai.com) and click **Sign up**. You can use your Google account or create one with your email address.

### 2b. Add a payment method

API usage is billed per report (see [What does it cost?](#what-does-it-cost) below — it's inexpensive). Before you can generate a key, OpenAI requires a payment method on file.

1. Log in at [platform.openai.com](https://platform.openai.com)
2. Click your organization name in the top-left corner
3. Go to **Billing** → **Payment methods**
4. Click **Add payment method** and enter a credit or debit card

You will not be charged until you actually generate reports. OpenAI only charges for what you use.

### 2c. Generate an API key

1. In the left sidebar, click **API keys**
2. Click **Create new secret key**
3. Give it a name (e.g., "Channel Intelligence")
4. Click **Create secret key**
5. **Copy the key now** — it starts with `sk-` and is about 50 characters long

> **Important:** This is the only time OpenAI shows you the full key. If you close this screen without copying it, you'll need to create a new one. Keep it somewhere safe — treat it like a password.

### 2d. Save your key to your computer

You need to save the key so the tool can find it automatically every time you run it.

**Mac:**

Open Terminal (`Command + Space`, type `Terminal`, press Enter). Run this command — replace `sk-...` with your actual key:

```
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.zshrc && source ~/.zshrc
```

To confirm it worked:
```
echo $OPENAI_API_KEY
```
You should see your key printed back. If you see a blank line, try closing Terminal and opening a new window, then check again.

**Windows:**

1. Press the Windows key, search for **Environment Variables**, click **Edit the system environment variables**
2. Click the **Environment Variables...** button
3. Under **User variables**, click **New**
4. Set **Variable name** to: `OPENAI_API_KEY`
5. Set **Variable value** to your key (the `sk-...` string)
6. Click **OK** on all windows
7. Close Command Prompt and open a new one — the key won't be recognized until you do

To confirm it worked, open a new Command Prompt and run:
```
echo %OPENAI_API_KEY%
```
You should see your key printed back.

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
