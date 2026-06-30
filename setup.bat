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

:: ── yt-dlp ────────────────────────────────────────────────────────────────
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
echo [Installing Python packages - openai and openai-whisper]
%PYTHON% -m pip install --quiet openai openai-whisper
if %errorlevel% neq 0 (
    echo   [X]  Package install failed.
    echo        Try running:  pip install openai openai-whisper
    set /a ERRORS+=1
) else (
    echo   [OK] openai and openai-whisper installed
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

:: ── OPENAI_API_KEY ─────────────────────────────────────────────────────────
:api_key
echo.
echo [Checking your OpenAI API key]
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
    echo        Then re-run this script to confirm it's working.
    set /a ERRORS+=1
) else (
    echo   [OK] OPENAI_API_KEY is set
)

:: ── Create reports directory ───────────────────────────────────────────────
if not exist reports mkdir reports

:: ── Summary ────────────────────────────────────────────────────────────────
:summary
echo.
echo +------------------------------------------+
if !ERRORS! equ 0 (
    echo ^|  All set! You are ready to go.          ^|
    echo +------------------------------------------+
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
