#!/usr/bin/env bash
# Channel Intelligence — First-time setup for Mac

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC}  $1"; }
fail() { echo -e "  ${RED}✗${NC}  $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "  ${YELLOW}!${NC}  $1"; }
step() { echo ""; echo -e "${BLUE}▶ $1${NC}"; }

ERRORS=0
HAVE_BREW=false

echo ""
echo "┌─────────────────────────────────────────┐"
echo "│   Channel Intelligence — Mac Setup      │"
echo "└─────────────────────────────────────────┘"
echo ""
echo "This walks you through everything needed to run the"
echo "Channel Intelligence tool for the first time."
echo ""
echo "It will check your system, install missing tools,"
echo "and tell you exactly what to do if anything needs"
echo "your attention."
echo ""
read -rp "Press Enter to start..."

# ── Python 3 ────────────────────────────────────────────────────────────────
step "Checking Python 3"
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    ok "Python $PYTHON_VERSION found"
else
    fail "Python 3 is not installed."
    echo ""
    echo "     Download and install it from:"
    echo "     https://www.python.org/downloads/"
    echo ""
    echo "     Then re-run this script."
    echo ""
    echo "Setup cannot continue without Python. Exiting."
    exit 1
fi

# ── pip ─────────────────────────────────────────────────────────────────────
step "Checking pip (Python package installer)"
if python3 -m pip --version &>/dev/null; then
    ok "pip is available"
else
    fail "pip is not available."
    echo "     Try running:  python3 -m ensurepip --upgrade"
fi

# ── Homebrew ─────────────────────────────────────────────────────────────────
step "Checking Homebrew (Mac package manager)"
if command -v brew &>/dev/null; then
    ok "Homebrew found"
    HAVE_BREW=true
else
    warn "Homebrew is not installed."
    echo ""
    echo "     Homebrew is the easiest way to install the tools this"
    echo "     project needs (yt-dlp, ffmpeg). To install it, paste"
    echo "     this into your terminal and press Enter:"
    echo ""
    echo "     /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    echo "     Then close this window, open a new terminal, and re-run"
    echo "     this script."
    echo ""
    echo "     (Continuing without Homebrew — some tools may not install.)"
fi

# ── yt-dlp ──────────────────────────────────────────────────────────────────
step "Checking yt-dlp (YouTube downloader)"
if command -v yt-dlp &>/dev/null; then
    ok "yt-dlp is already installed"
elif [ "$HAVE_BREW" = true ]; then
    echo "     Installing yt-dlp via Homebrew..."
    if brew install yt-dlp &>/dev/null; then
        ok "yt-dlp installed"
    else
        fail "yt-dlp install failed. Try running:  brew install yt-dlp"
    fi
else
    echo "     Installing yt-dlp via pip..."
    if python3 -m pip install --quiet yt-dlp; then
        ok "yt-dlp installed"
    else
        fail "yt-dlp install failed. Try running:  pip3 install yt-dlp"
    fi
fi

# ── ffmpeg ───────────────────────────────────────────────────────────────────
step "Checking ffmpeg (audio processing)"
if command -v ffmpeg &>/dev/null; then
    ok "ffmpeg is already installed"
elif [ "$HAVE_BREW" = true ]; then
    echo "     Installing ffmpeg via Homebrew (this takes a few minutes)..."
    if brew install ffmpeg &>/dev/null; then
        ok "ffmpeg installed"
    else
        fail "ffmpeg install failed. Try running:  brew install ffmpeg"
    fi
else
    fail "ffmpeg is not installed, and Homebrew is not available."
    echo "     Once Homebrew is installed, run:  brew install ffmpeg"
fi

# ── Provider selection ────────────────────────────────────────────────────────
step "Choosing your AI provider"
if [ -n "$LLM_MODEL" ]; then
    _MODEL="$LLM_MODEL"
    ok "Using provider from environment: $_MODEL"
else
    echo ""
    echo "  Which AI provider would you like to use to generate reports?"
    echo "  You can change this later by editing LLM_MODEL in config.py."
    echo ""
    echo "    1) OpenAI gpt-4o-mini          (default, ~\$1–3 per report)"
    echo "    2) Anthropic claude-haiku-4-5  (fast and affordable, ~\$0.50–2 per report)"
    echo "    3) Google gemini-1.5-flash     (generous free tier, ~\$0.10–1 per report)"
    echo "    4) Ollama (local, free)        (runs on your machine, no API key needed)"
    echo ""
    read -rp "  Enter 1–4 [1]: " _choice
    _choice="${_choice:-1}"

    case "$_choice" in
        2) _MODEL="anthropic/claude-haiku-4-5" ;;
        3) _MODEL="gemini/gemini-1.5-flash" ;;
        4) _MODEL="ollama/llama3.2" ;;
        *) _MODEL="gpt-4o-mini" ;;
    esac

    python3 - "$_MODEL" <<'PYEOF'
import sys
model = sys.argv[1]
with open('config.py', 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'LLM_MODEL = os.environ.get' in line:
        lines[i] = f'LLM_MODEL = os.environ.get("LLM_MODEL", "{model}")\n'
        break
with open('config.py', 'w') as f:
    f.writelines(lines)
PYEOF
    if [ $? -eq 0 ]; then
        ok "Provider set to $_MODEL (saved to config.py)"
    else
        warn "Could not update config.py automatically."
        echo "     Open config.py and change the LLM_MODEL default to: \"$_MODEL\""
    fi
    export LLM_MODEL="$_MODEL"
fi

# ── Python packages ──────────────────────────────────────────────────────────
step "Installing Python packages"
echo "     Installing litellm, openai, and openai-whisper..."
if python3 -m pip install --quiet litellm openai openai-whisper; then
    ok "litellm, openai, and openai-whisper installed"
else
    fail "Package install failed."
    echo "     Try running:  pip3 install litellm openai openai-whisper"
fi

# Install provider-specific SDK based on chosen provider
if [[ "$_MODEL" == anthropic/* ]]; then
    echo "     LLM_MODEL is Anthropic — installing anthropic SDK..."
    python3 -m pip install --quiet anthropic && ok "anthropic installed" || warn "anthropic install failed. Run: pip3 install anthropic"
elif [[ "$_MODEL" == gemini/* ]]; then
    echo "     LLM_MODEL is Google — installing google-genai SDK..."
    python3 -m pip install --quiet google-genai && ok "google-genai installed" || warn "google-genai install failed. Run: pip3 install google-genai"
fi

# ── whisper command ──────────────────────────────────────────────────────────
step "Checking whisper (audio transcription)"
if command -v whisper &>/dev/null; then
    ok "whisper is available"
else
    # pip installs whisper into a bin directory that may not be on PATH yet
    WHISPER_PATH=$(python3 -c "import site, os; dirs = site.getsitepackages(); print(next((os.path.join(d, '..', '..', '..', 'bin') for d in dirs), ''))" 2>/dev/null)
    if [ -f "$WHISPER_PATH/whisper" ]; then
        warn "whisper is installed but not yet on your PATH."
        echo "     Add this line to your ~/.zshrc, then restart your terminal:"
        echo ""
        echo "     export PATH=\"$WHISPER_PATH:\$PATH\""
        echo ""
        ERRORS=$((ERRORS + 1))
    else
        warn "whisper command not found. Try closing this terminal and opening a new one."
        echo "     If it still doesn't appear, run:"
        echo "     pip3 install openai-whisper"
        ERRORS=$((ERRORS + 1))
    fi
fi

# ── API key check (provider-aware) ───────────────────────────────────────────
step "Checking your AI provider API key"

if [[ "$_MODEL" == anthropic/* ]]; then
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        ok "ANTHROPIC_API_KEY is set (Anthropic provider)"
    else
        fail "ANTHROPIC_API_KEY is not set."
        echo ""
        echo "     Get an Anthropic API key at: https://console.anthropic.com/"
        echo "     Then run:"
        echo "     echo 'export ANTHROPIC_API_KEY=\"sk-ant-...\"' >> ~/.zshrc"
        echo "     source ~/.zshrc"
    fi
elif [[ "$_MODEL" == gemini/* ]]; then
    if [ -n "$GEMINI_API_KEY" ]; then
        ok "GEMINI_API_KEY is set (Google provider)"
    else
        fail "GEMINI_API_KEY is not set."
        echo ""
        echo "     Get a Google API key at: https://aistudio.google.com/apikey"
        echo "     Then run:"
        echo "     echo 'export GEMINI_API_KEY=\"AI...\"' >> ~/.zshrc"
        echo "     source ~/.zshrc"
    fi
elif [[ "$_MODEL" == ollama/* ]]; then
    if curl -s http://localhost:11434 &>/dev/null; then
        ok "Ollama is running locally (no API key needed)"
    else
        fail "Ollama does not appear to be running."
        echo ""
        echo "     Download Ollama at: https://ollama.com"
        echo "     Then pull your model, for example:"
        echo "     ollama pull llama3.2"
        echo "     And make sure Ollama is running before generating reports."
    fi
else
    if [ -n "$OPENAI_API_KEY" ]; then
        ok "OPENAI_API_KEY is set (OpenAI provider)"
    else
        fail "OPENAI_API_KEY is not set."
        echo ""
        echo "     You need an OpenAI API key to generate reports."
        echo "     Get one at:  https://platform.openai.com/api-keys"
        echo ""
        echo "     Once you have your key, run these two commands"
        echo "     (replace sk-... with your actual key):"
        echo ""
        echo "     echo 'export OPENAI_API_KEY=\"sk-...\"' >> ~/.zshrc"
        echo "     source ~/.zshrc"
        echo ""
        echo "     Then re-run this script to confirm it's working."
        echo ""
        echo "     To use a different provider instead, re-run this script"
        echo "     and choose a different option at the provider step."
    fi
fi

# ── Create reports directory ─────────────────────────────────────────────────
mkdir -p reports

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "┌─────────────────────────────────────────┐"
if [ $ERRORS -eq 0 ]; then
    echo -e "│  ${GREEN}All set! You're ready to go.${NC}           │"
    echo "└─────────────────────────────────────────┘"
    echo ""
    echo "  AI provider: $_MODEL"
    echo "  To change later: edit LLM_MODEL in config.py"
    echo ""
    echo "  To generate your first report, run:"
    echo ""
    echo "    python3 agent.py https://www.youtube.com/@CompanyName/videos"
    echo ""
    echo "  Replace CompanyName with the YouTube channel you want to analyze."
    echo "  Your report will appear in the reports/ folder when it's done."
    echo ""
    echo "  The first run takes 30–90 minutes depending on how many videos"
    echo "  the channel has. Re-runs on the same channel are much faster."
else
    echo -e "│  ${YELLOW}Setup incomplete — $ERRORS item(s) need attention.${NC}"
    echo "└─────────────────────────────────────────┘"
    echo ""
    echo "  Fix the items marked with ✗ above, then re-run this script."
    echo "  Each check will pass once the issue is resolved."
fi
echo ""
