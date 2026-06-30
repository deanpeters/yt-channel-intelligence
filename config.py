import os

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

LLM_MODEL = "gpt-4o-mini"

LOOKBACK_MONTHS = 30
MAX_VIDEOS      = 50        # cap per run; yt-dlp returns newest-first so this keeps the most recent
WHISPER_MODEL   = "medium.en"
AUDIO_FORMAT    = "m4a"

DATA_DIR    = ".workspace"
REPORTS_DIR = "reports"
