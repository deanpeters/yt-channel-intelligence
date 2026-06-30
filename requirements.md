# Requirements

## Python packages

```bash
pip install litellm openai openai-whisper
```

Add the SDK for your chosen provider if not using OpenAI:

```bash
pip install anthropic        # if using Anthropic
pip install google-genai     # if using Google Gemini
# Ollama: no extra package — LiteLLM talks to it via HTTP
```

## System tools

These must be installed separately before running the agent:

| Tool | What it does | Install |
|---|---|---|
| `yt-dlp` | Downloads video metadata and audio from YouTube | `brew install yt-dlp` |
| `ffmpeg` | Audio processing | `brew install ffmpeg` |

## Environment variables

Set `LLM_MODEL` and the matching API key for your chosen provider:

| Provider | `LLM_MODEL` | API key variable |
|---|---|---|
| OpenAI (default) | `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| Google | `gemini/gemini-1.5-flash` | `GEMINI_API_KEY` |
| Ollama (local) | `ollama/llama3.2` | *(none — runs locally)* |

`LLM_MODEL` defaults to `gpt-4o-mini` if not set. To change it:

```bash
export LLM_MODEL="anthropic/claude-haiku-4-5"
export ANTHROPIC_API_KEY="sk-ant-..."
```
