@echo off
setlocal enabledelayedexpansion

echo.
echo +------------------------------------------+
echo ^|  Channel Intelligence -- Windows Setup   ^|
echo +------------------------------------------+
echo.
echo This walks you through everything needed to run the
echo Channel Intelligence tool for the first time.
echo.
echo It will check your system, install missing tools,
echo and tell you exactly what to do if anything needs
echo your attention.
echo.
pause

set ERRORS=0
set PYTHON=

:: ── Python 3 ──────────────────────────────────────────────────────────────
echo.
echo [Checking Python 3]
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   [OK]  Python %%v found
    goto :pip_check
)
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python3
    for /f "tokens=2" %%v in ('python3 --version 2^>^&1') do echo   [OK]  Python %%v found
    goto :pip_check
)
echo   [X]  Python is not installed.
echo.
echo        Download and install it from:
echo        https://www.python.org/downloads/
echo.
echo        IMPORTANT: On the install screen, check the box that says
echo        "Add Python to PATH" before clicking Install Now.
echo.
echo        Then close this window, open a new Command Prompt,
echo        and re-run this script.
echo.
echo Setup cannot continue without Python. Exiting.
set ERRORS=1
goto :summary

:: ── pip ───────────────────────────────────────────────────────────────────
:pip_check
echo.
echo [Checking pip]
%PYTHON% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X]  pip is not available.
    echo        Try running:  %PYTHON% -m ensurepip --upgrade
    set /a ERRORS+=1
) else (
    echo   [OK] pip is available
)

:: ── Provider selection ──────────────────────────────────────────────────────
echo.
echo [Choosing your AI provider]
if not "%LLM_MODEL%"=="" (
    set _MODEL=%LLM_MODEL%
    echo   [OK] Using provider from environment: %LLM_MODEL%
    goto :install_yt_dlp
)
echo.
echo   Which AI provider would you like to use to generate reports?
echo   You can change this later by editing LLM_MODEL in config.py.
echo.
echo     1) OpenAI gpt-4o-mini          (default, ~$1-3 per report)
echo     2) Anthropic claude-haiku-4-5  (fast and affordable, ~$0.50-2 per report)
echo     3) Google gemini-1.5-flash     (generous free tier, ~$0.10-1 per report)
echo     4) Ollama (local, free)        (runs on your machine, no API key needed)
echo.
choice /C 1234 /N /M "  Enter 1-4 [press 1 for default]: "
if %errorlevel% equ 2 set _MODEL=anthropic/claude-haiku-4-5
if %errorlevel% equ 3 set _MODEL=gemini/gemini-1.5-flash
if %errorlevel% equ 4 set _MODEL=ollama/llama3.2
if %errorlevel% equ 1 set _MODEL=gpt-4o-mini
if "%_MODEL%"=="" set _MODEL=gpt-4o-mini

:: Save to config.py using Python (avoids batch quoting nightmares)
echo model = '%_MODEL%'                                        > "%TEMP%\ucfg.py"
echo lines = open('config.py').readlines()                   >> "%TEMP%\ucfg.py"
echo out = []                                                >> "%TEMP%\ucfg.py"
echo for line in lines:                                      >> "%TEMP%\ucfg.py"
echo     if 'LLM_MODEL = os.environ.get' in line:           >> "%TEMP%\ucfg.py"
echo         q = chr(34)                                     >> "%TEMP%\ucfg.py"
echo         out.append(f'LLM_MODEL = os.environ.get({q}LLM_MODEL{q}, {q}{model}{q})\n') >> "%TEMP%\ucfg.py"
echo     else:                                               >> "%TEMP%\ucfg.py"
echo         out.append(line)                                >> "%TEMP%\ucfg.py"
echo open('config.py', 'w').writelines(out)                 >> "%TEMP%\ucfg.py"
%PYTHON% "%TEMP%\ucfg.py" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Provider set to %_MODEL% (saved to config.py^)
) else (
    echo   [!]  Could not update config.py automatically.
    echo        Open config.py and set LLM_MODEL default to: %_MODEL%
)
del "%TEMP%\ucfg.py" >nul 2>&1

:: ── yt-dlp ────────────────────────────────────────────────────────────────
:install_yt_dlp
echo.
echo [Installing yt-dlp - YouTube downloader]
yt-dlp --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] yt-dlp is already installed
) else (
    %PYTHON% -m pip install --quiet yt-dlp
    if %errorlevel% neq 0 (
        echo   [X]  yt-dlp install failed.
        echo        Try running:  pip install yt-dlp
        set /a ERRORS+=1
    ) else (
        echo   [OK] yt-dlp installed
    )
)

:: ── Python packages ────────────────────────────────────────────────────────
echo.
echo [Installing Python packages - litellm, openai, and openai-whisper]
%PYTHON% -m pip install --quiet litellm openai openai-whisper
if %errorlevel% neq 0 (
    echo   [X]  Package install failed.
    echo        Try running:  pip install litellm openai openai-whisper
    set /a ERRORS+=1
) else (
    echo   [OK] litellm, openai, and openai-whisper installed
)

:: Install provider SDK based on chosen provider
echo %_MODEL% | findstr /b "anthropic/" >nul 2>&1
if %errorlevel% equ 0 (
    echo        Installing Anthropic SDK...
    %PYTHON% -m pip install --quiet anthropic
    if %errorlevel% equ 0 (echo   [OK] anthropic installed) else (echo   [!]  anthropic install failed. Run: pip install anthropic)
)
echo %_MODEL% | findstr /b "gemini/" >nul 2>&1
if %errorlevel% equ 0 (
    echo        Installing Google SDK...
    %PYTHON% -m pip install --quiet google-genai
    if %errorlevel% equ 0 (echo   [OK] google-genai installed) else (echo   [!]  google-genai install failed. Run: pip install google-genai)
)

:: ── ffmpeg ─────────────────────────────────────────────────────────────────
echo.
echo [Checking ffmpeg - audio processing]
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] ffmpeg is already installed
    goto :api_key
)
echo        ffmpeg not found. Trying to install via winget...
winget install --id Gyan.FFmpeg --silent >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] ffmpeg installed via winget
    echo        You may need to restart your terminal for ffmpeg to be recognized.
) else (
    echo   [X]  ffmpeg is not installed and automatic install failed.
    echo.
    echo        To install ffmpeg manually:
    echo        1. Go to https://www.gyan.dev/ffmpeg/builds/
    echo        2. Download "ffmpeg-release-essentials.zip"
    echo        3. Extract the zip file
    echo        4. Copy ffmpeg.exe from the bin\ folder to C:\Windows\System32\
    echo.
    echo        After that, close this window, open a new Command Prompt,
    echo        and re-run this script.
    set /a ERRORS+=1
)

:: ── API key check (provider-aware) ─────────────────────────────────────────
:api_key
echo.
echo [Checking your AI provider API key]

if "%_MODEL%"=="" set _MODEL=gpt-4o-mini

echo %_MODEL% | findstr /b "anthropic/" >nul 2>&1
if %errorlevel% equ 0 (
    if "%ANTHROPIC_API_KEY%"=="" (
        echo   [X]  ANTHROPIC_API_KEY is not set.
        echo        Get a key at: https://console.anthropic.com/
        echo        Set it in System Environment Variables as ANTHROPIC_API_KEY
        set /a ERRORS+=1
    ) else (
        echo   [OK] ANTHROPIC_API_KEY is set (Anthropic provider^)
    )
    goto :create_dirs
)

echo %_MODEL% | findstr /b "gemini/" >nul 2>&1
if %errorlevel% equ 0 (
    if "%GEMINI_API_KEY%"=="" (
        echo   [X]  GEMINI_API_KEY is not set.
        echo        Get a key at: https://aistudio.google.com/apikey
        echo        Set it in System Environment Variables as GEMINI_API_KEY
        set /a ERRORS+=1
    ) else (
        echo   [OK] GEMINI_API_KEY is set (Google provider^)
    )
    goto :create_dirs
)

echo %_MODEL% | findstr /b "ollama/" >nul 2>&1
if %errorlevel% equ 0 (
    curl -s http://localhost:11434 >nul 2>&1
    if %errorlevel% equ 0 (
        echo   [OK] Ollama is running locally (no API key needed^)
    ) else (
        echo   [X]  Ollama does not appear to be running.
        echo        Download it at: https://ollama.com
        echo        Then run: ollama pull llama3.2
        set /a ERRORS+=1
    )
    goto :create_dirs
)

:: Default: OpenAI
if "%OPENAI_API_KEY%"=="" (
    echo   [X]  OPENAI_API_KEY is not set.
    echo.
    echo        You need an OpenAI API key to generate reports.
    echo        Get one at:  https://platform.openai.com/api-keys
    echo.
    echo        To set it permanently on Windows:
    echo        1. Press the Windows key, search for "Environment Variables"
    echo        2. Click "Edit the system environment variables"
    echo        3. Click the "Environment Variables..." button
    echo        4. Under "User variables", click "New"
    echo        5. Variable name:   OPENAI_API_KEY
    echo           Variable value:  sk-... (paste your actual key here^)
    echo        6. Click OK on all windows
    echo        7. Close and reopen this terminal
    echo.
    echo        To use a different provider instead, set LLM_MODEL before
    echo        re-running. See SETUP.md for all provider options.
    set /a ERRORS+=1
) else (
    echo   [OK] OPENAI_API_KEY is set (OpenAI provider^)
)

:: ── Create reports directory ───────────────────────────────────────────────
:create_dirs
if not exist reports mkdir reports

:: ── Summary ────────────────────────────────────────────────────────────────
:summary
echo.
echo +------------------------------------------+
if !ERRORS! equ 0 (
    echo ^|  All set! You are ready to go.          ^|
    echo +------------------------------------------+
    echo.
    echo   AI provider: %_MODEL%
    echo   To change later: edit LLM_MODEL in config.py
    echo.
    echo   To generate your first report, run:
    echo.
    echo     python agent.py https://www.youtube.com/@CompanyName/videos
    echo.
    echo   Replace CompanyName with the YouTube channel you want to analyze.
    echo   Your report will appear in the reports\ folder when it's done.
    echo.
    echo   The first run takes 30-90 minutes depending on how many videos
    echo   the channel has. Re-runs on the same channel are much faster.
) else (
    echo ^|  Setup incomplete -- see issues above.   ^|
    echo +------------------------------------------+
    echo.
    echo   Fix the items marked [X] above, then re-run this script.
    echo   Each check will pass once the issue is resolved.
)
echo.
pause
