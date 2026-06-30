import os

# Which model to use for AI synthesis. The provider is encoded in the model string:
#   OpenAI (default):  gpt-4o-mini  or  gpt-4o
#   Anthropic:         anthropic/claude-haiku-4-5  or  anthropic/claude-sonnet-4-6
#   Google:            gemini/gemini-1.5-flash  or  gemini/gemini-2.0-flash
#   Ollama (local):    ollama/llama3.2  or  ollama/mistral
#
# Set the matching environment variable for your provider:
#   OpenAI:    OPENAI_API_KEY
#   Anthropic: ANTHROPIC_API_KEY
#   Google:    GEMINI_API_KEY
#   Ollama:    none — runs locally, no key needed
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

LOOKBACK_MONTHS = 30
MAX_VIDEOS      = 50        # cap per run; yt-dlp returns newest-first so this keeps the most recent
WHISPER_MODEL   = "medium.en"
AUDIO_FORMAT    = "m4a"

DATA_DIR    = ".workspace"
REPORTS_DIR = "reports"
