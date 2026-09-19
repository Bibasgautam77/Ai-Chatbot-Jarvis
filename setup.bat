@echo off
REM One-time setup: creates a virtual environment and installs dependencies.
REM Double-click this file once before using run_jarvis.bat / run_jarvis_voice.bat

cd /d "%~dp0"

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo.
    echo Could not create a virtual environment. Make sure Python is installed
    echo and added to PATH ^(check "Add Python to PATH" during install^).
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================================
echo Setup complete.
echo.
echo Before running Jarvis, set your Anthropic API key:
echo     setx ANTHROPIC_API_KEY "sk-ant-your-key-here"
echo ^(then open a NEW terminal window so it takes effect^)
echo.
echo Then double-click run_jarvis.bat ^(text mode^) or
echo run_jarvis_voice.bat ^(voice mode^) to start.
echo ============================================================
pause
