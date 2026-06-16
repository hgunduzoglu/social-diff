#!/bin/bash
# Social Diff - macOS launcher (double-clickable from Finder).
# Finds a Tk-capable Python, builds a local .venv, installs selenium, runs the GUI.
set -e
cd "$(dirname "$0")"

echo "=== Social Diff ==="

find_python() {
  # Need a Python with a MODERN Tk (>= 8.6). macOS system Tk is 8.5 and renders
  # blank windows on recent macOS, so we explicitly reject it.
  for cand in /opt/homebrew/bin/python3 \
              /usr/local/bin/python3 \
              /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
              python3 \
              /usr/bin/python3; do
    if "$cand" -c "import sys,tkinter; sys.exit(0 if tkinter.TkVersion>=8.6 else 1)" >/dev/null 2>&1; then
      echo "$cand"; return 0
    fi
  done
  return 1
}

if [ ! -d ".venv" ]; then
  PY="$(find_python)" || {
    echo "ERROR: No Python with a modern Tk (>= 8.6) found."
    echo "Install it with:  brew install python-tk"
    echo "(or use the python.org installer, which includes Tk 8.6)."
    read -n 1 -s -r -p "Press any key to close..."; exit 1
  }
  echo "Creating virtual environment with: $PY"
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import selenium" >/dev/null 2>&1; then
  echo "Installing selenium (first run only)..."
  pip install --quiet --upgrade pip
  pip install --quiet selenium
fi

echo "Launching..."
python app.py

echo
read -n 1 -s -r -p "Closed. Press any key to exit..."
