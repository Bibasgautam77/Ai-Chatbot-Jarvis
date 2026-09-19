@echo off
REM Double-click this to start Jarvis in text mode.
REM Run setup.bat first if you haven't already.

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found -- run setup.bat first.
    pause
    exit /b 1
)

if "%ANTHROPIC_API_KEY%"=="" (
    echo.
    echo WARNING: ANTHROPIC_API_KEY is not set in this environment.
    echo Run: setx ANTHROPIC_API_KEY "sk-ant-your-key-here"
    echo then open a new terminal and try again.
    echo.
    pause
)

python main.py

pause
