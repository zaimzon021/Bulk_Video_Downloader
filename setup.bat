@echo off
echo ================================
echo  YouTube Downloader - Setup
echo ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Installing Python dependencies...
pip install yt-dlp --quiet
echo Done.

echo.
echo [2/2] Checking required files...

if not exist "yt-dlp.exe" (
    echo [WARN] yt-dlp.exe not found. Downloading...
    curl -L "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -o yt-dlp.exe
)

if not exist "deno.exe" (
    echo [WARN] deno.exe not found in folder.
    echo        Download from https://deno.land and place deno.exe here.
)

if not exist "ffmpeg.exe" (
    echo [WARN] ffmpeg.exe not found in folder.
    echo        Download from https://ffmpeg.org and place ffmpeg.exe here.
)

if not exist "cookies.txt" (
    echo [WARN] cookies.txt not found.
    echo        Export from YouTube using the "Get cookies.txt LOCALLY" Chrome extension.
)

echo.
echo ================================
echo  Setup complete! Run: python app.py
echo ================================
pause
