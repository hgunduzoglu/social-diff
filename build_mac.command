#!/bin/bash
# Build a standalone macOS .app (dist/SocialDiff.app).
# Run this once; afterwards you can double-click the .app like any other app.
set -e
cd "$(dirname "$0")"

find_python() {
  for cand in /opt/homebrew/bin/python3 /usr/local/bin/python3 python3 /usr/bin/python3; do
    if "$cand" -c "import sys,tkinter; sys.exit(0 if tkinter.TkVersion>=8.6 else 1)" >/dev/null 2>&1; then
      echo "$cand"; return 0
    fi
  done
  return 1
}

if [ ! -d ".venv" ]; then
  PY="$(find_python)" || { echo "No Tk-capable Python. brew install python-tk"; exit 1; }
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install selenium pyinstaller

pyinstaller --noconfirm --windowed --name SocialDiff \
  --collect-all selenium \
  --add-data "scrape.py:." \
  --add-data "compare.py:." \
  app.py

echo
echo "Done. Your app is in: dist/SocialDiff.app"
read -n 1 -s -r -p "Press any key to close..."
