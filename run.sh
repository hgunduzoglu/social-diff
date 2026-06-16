#!/bin/bash
# Social Diff - Linux launcher.
# Finds a Tk-capable Python, builds a local .venv, installs selenium, runs the GUI.
#   chmod +x run.sh   (once)   then:   ./run.sh
set -e
cd "$(dirname "$0")"

echo "=== Social Diff ==="

find_python() {
  # Need a Python with a modern Tk (>= 8.6) and the tkinter module.
  for cand in python3 /usr/bin/python3 /usr/local/bin/python3; do
    if command -v "$cand" >/dev/null 2>&1 && \
       "$cand" -c "import sys,tkinter; sys.exit(0 if tkinter.TkVersion>=8.6 else 1)" >/dev/null 2>&1; then
      echo "$cand"; return 0
    fi
  done
  return 1
}

if [ ! -d ".venv" ]; then
  PY="$(find_python)" || {
    echo "ERROR: No Python with tkinter found."
    echo "Install it, e.g.:"
    echo "  Debian/Ubuntu : sudo apt install python3 python3-venv python3-tk"
    echo "  Fedora        : sudo dnf install python3 python3-tkinter"
    echo "  Arch          : sudo pacman -S python tk"
    echo "Google Chrome (or Chromium) must also be installed."
    exit 1
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
