# Social Diff

Compare your **followers vs. following** on Instagram and Twitter/X and get a
**two-way mismatch** list:

- **Don't follow you back** — you follow them, they don't follow you.
- **You don't follow back** — they follow you, you don't follow them.

## How it works

1. A Chrome window opens. **You log in yourself** (2FA / checkpoint included —
   no time limit).
2. You click **"I'm logged in → Fetch lists"**.
3. The script visits your profile, scrolls the followers/following dialogs,
   collects the handles, compares them, shows the result and saves `.txt` files.

Login is saved in a local `chrome-profile/` folder, so next time you're already
logged in.

## Running

### macOS
Double-click **`run.command`** (first run builds a local environment and installs
Selenium automatically).

### Windows
Double-click **`run.bat`** (same idea).

> Requires Google Chrome installed. Selenium downloads the matching driver
> automatically.

## Building a standalone app (optional)

- **Windows .exe:** run `build_windows.bat` → `dist\SocialDiff\SocialDiff.exe`
- **macOS .app:** run `build_mac.command` → `dist/SocialDiff.app`

## Files

| file | purpose |
|------|---------|
| `app.py` | the GUI |
| `scrape.py` | Selenium collector (also usable from the CLI) |
| `compare.py` | comparison logic (also usable from the CLI) |
| `run.command` / `run.bat` | double-click launchers |
| `build_*.command` / `build_*.bat` | build standalone apps |

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
