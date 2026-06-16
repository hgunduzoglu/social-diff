@echo off
REM Social Diff - Windows launcher (double-click from Explorer).
REM Builds a local .venv, installs selenium, runs the GUI.
cd /d "%~dp0"
title Social Diff

echo === Social Diff ===

if not exist ".venv\" (
  where py >nul 2>&1
  if %errorlevel%==0 (
    set "PY=py -3"
  ) else (
    set "PY=python"
  )
  echo Creating virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo ERROR: Could not create venv. Install Python from https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH" and "tcl/tk" during install.
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat

python -c "import selenium" >nul 2>&1
if errorlevel 1 (
  echo Installing selenium ^(first run only^)...
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet selenium
)

echo Launching...
python app.py

echo.
pause
