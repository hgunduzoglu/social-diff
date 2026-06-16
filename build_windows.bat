@echo off
REM Build a standalone Windows .exe (dist\SocialDiff\SocialDiff.exe).
REM Run this once on a Windows machine that has Python installed.
cd /d "%~dp0"

if not exist ".venv\" (
  py -3 -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install selenium pyinstaller

pyinstaller --noconfirm --windowed --name SocialDiff ^
  --collect-all selenium ^
  --add-data "scrape.py;." ^
  --add-data "compare.py;." ^
  app.py

echo.
echo Done. Your app is in: dist\SocialDiff\SocialDiff.exe
echo (Share the whole dist\SocialDiff folder, or zip it.)
pause
