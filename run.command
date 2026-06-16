#!/bin/bash
# Social Diff - macOS launcher (double-clickable from Finder).
# Finds a Tk-capable Python, builds a local .venv, installs selenium, runs the GUI.
set -e
cd "$(dirname "$0")"

echo "=== Social Diff ==="

find_python() {
  # Prefer an interpreter that actually has tkinter (pyenv builds often don't).
  for cand in /usr/bin/python3 \
              /opt/homebrew/bin/python3 \
              /usr/local/bin/python3 \
              /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
              python3; do
    if "$cand" -c "import tkinter" >/dev/null 2>&1; then
      echo "$cand"; return 0
    fi
  done
  return 1
}

if [ ! -d ".venv" ]; then
  PY="$(find_python)" || {
    echo "ERROR: No Python with tkinter found."
    echo "Install it with:  brew install python-tk"
    echo "(or use the python.org installer, which includes Tk)."
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
