# Social Diff

**English** · [Türkçe](README.tr.md)

Compares followers vs. following on Instagram and Twitter/X and produces a
**two-way mismatch** list:

- **Don't follow you back** — you follow them, they don't follow you back.
- **You don't follow back** — they follow you, you don't follow them back.

## How it works

1. On launch you see two big buttons: **Instagram** and **Twitter / X**. Click one
   to open that platform's screen.
2. Type your username, click **"Open browser"** → a Chrome window opens and **you
   log in yourself** (2FA / checkpoint included, no time limit).
3. Click **"I'm logged in → Fetch lists"** → the script visits your profile,
   scrolls the followers/following lists, collects the handles, compares them,
   shows the result on screen and saves `.txt` files.
4. You can **"Stop"** (or go **"Back"**) at any time; that also closes the Chrome
   window.

Your login is stored in a local `chrome-profile/` folder, so next time you're
already logged in.

## Download

```bash
git clone https://github.com/hgunduzoglu/social-diff.git
```

or grab it from the GitHub interface via **Download ZIP** and unzip.

## Requirements

- **Google Chrome** (or Chromium) installed — Selenium downloads the matching driver.
- **Python 3** (with Tk 8.6+). The launchers build a local virtual environment and
  install Selenium automatically on first run.

## Running

| OS | What to do |
|----|------------|
| **macOS** | Double-click `run.command`. If no Tk-capable Python: `brew install python-tk` |
| **Windows** | Double-click `run.bat` |
| **Linux** | In a terminal: `./run.sh` (first `chmod +x run.sh`). If needed: `sudo apt install python3-venv python3-tk` |

## Standalone app (optional)

- **Windows .exe:** run `build_windows.bat` → `dist\SocialDiff\SocialDiff.exe`
- **macOS .app:** run `build_mac.command` → `dist/SocialDiff.app`

## Files

| file | purpose |
|------|---------|
| `app.py` | the GUI |
| `scrape.py` | Selenium collector (also usable from the CLI) |
| `compare.py` | comparison logic (also usable from the CLI) |
| `run.command` / `run.bat` / `run.sh` | launchers (macOS / Windows / Linux) |
| `build_windows.bat` / `build_mac.command` | build standalone apps |

## Command-line (optional)

```bash
python scrape.py instagram YOUR_USERNAME
python scrape.py twitter   YOUR_USERNAME
python compare.py --following-list instagram_following.txt \
                  --followers-list instagram_followers.txt \
                  --platform Instagram --save result_instagram
```

## Notes

- Scraping social sites is against their ToS; use your own account at your own
  risk and don't run it repeatedly (rate limits).
- If a site changes its HTML, the CSS selectors in `scrape.py` may need updating.