@echo off
rem Build VideoGrab into a portable folder dist\VideoGrab (ASCII-only: cmd reads bat as cp866)
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo [!] .venv not found. Run:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

rem ffmpeg не вшивается (~200 МБ): приложение скачивает его кнопкой «Скачать ffmpeg»
rem (для разработки берётся из vendor\ffmpeg или PATH)
set FFMPEG_FLAGS=

.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --noconsole --name VideoGrab --icon assets\icon.ico --add-data "assets\icon.ico;assets" --collect-all customtkinter --collect-all pystray %FFMPEG_FLAGS% app.py
if errorlevel 1 (
    echo [x] Build failed.
    exit /b 1
)

if exist README_user.txt copy /y README_user.txt dist\VideoGrab\README.txt >nul

echo.
echo Done! Portable app: dist\VideoGrab\VideoGrab.exe
endlocal
