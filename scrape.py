#!/usr/bin/env python3
"""
scrape.py - Instagram / Twitter(X) takipci + takip listesi toplayici (Selenium)

Mantik:
  - Tarayiciyi acar, SEN ELLE giris yaparsin (2FA / checkpoint dahil).
  - ENTER'a basinca script profile gidip followers + following listesini
    scroll ederek toplar ve .txt olarak yazar.
  - Kalici Chrome profili (--profile-dir) kullanir; ikinci calistirmada zaten login'sin.

Kullanim:
  pip install selenium                 # Chrome zaten kurulu olmali (driver'i Selenium otomatik indirir)

  python scrape.py instagram KULLANICI_ADIN
  python scrape.py twitter   KULLANICI_ADIN

Cikti:  {platform}_following.txt  ve  {platform}_followers.txt
        (compare.py'ye --following-list / --followers-list olarak verilebilir)

NOT: ToS'a aykiridir, hesap riski sifir degildir (ozellikle IG). DOM selektorleri
     degisebilir; biri patlarsa ilgili CSS selektorunu guncelle. Art arda cok
     calistirma -> rate limit.
"""

import argparse
import re
import sys
import time
from pathlib import Path

# --------------------------------------------------------------- saf yardimcilar (test edildi)

IG_RESERVED = {"explore", "reels", "reel", "p", "accounts", "direct", "stories", "tv",
               "about", "legal", "privacy", "developer", "directory", "web", "emails",
               "challenge", "oauth", "ajax", "followers", "following"}

TW_RESERVED = {"home", "explore", "notifications", "messages", "i", "settings", "search",
               "compose", "hashtag", "tos", "privacy", "login", "logout", "signup", "about",
               "intent", "share", "account", "bookmarks", "lists", "topics", "jobs",
               "verified_followers", "follower_requests"}


def clean_ig_handle(href):
    if not href:
        return None
    m = re.sub(r"^https?://(www\.)?instagram\.com", "", href, flags=re.I)
    m = m.split("?")[0].split("#")[0].strip()
    parts = [p for p in m.split("/") if p]
    if len(parts) != 1:
        return None
    u = parts[0]
    return None if u.lower() in IG_RESERVED else u


def clean_tw_handle(href):
    if not href:
        return None
    m = re.sub(r"^https?://(www\.)?(x|twitter)\.com", "", href, flags=re.I)
    m = m.split("?")[0].split("#")[0].strip()
    if "/status/" in m or "/i/" in m:
        return None
    parts = [p for p in m.split("/") if p]
    if len(parts) != 1:
        return None
    u = parts[0]
    if u.lower() in TW_RESERVED:
        return None
    return u if re.fullmatch(r"[A-Za-z0-9_]{1,15}", u) else None


# --------------------------------------------------------------- selenium kurulum

def build_driver(profile_dir, headless=False):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        raise RuntimeError("selenium kurulu degil:  pip install selenium")

    opts = Options()
    # bot tespitini azaltan bayraklar
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(f"--user-data-dir={Path(profile_dir).resolve()}")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--lang=en-US")
    if headless:
        opts.add_argument("--headless=new")  # IG'de headless genelde checkpoint yer; onerilmez

    driver = webdriver.Chrome(options=opts)
    # navigator.webdriver = undefined
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    return driver

    # IG seni yine bloklarsa: vanilla selenium yerine undetected-chromedriver dene
    #   pip install undetected-chromedriver
    #   import undetected_chromedriver as uc
    #   driver = uc.Chrome(user_data_dir=profile_dir)


# --------------------------------------------------------------- toplama cekirdegi

def _hrefs_in(driver, css):
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import StaleElementReferenceException
    out = []
    for e in driver.find_elements(By.CSS_SELECTOR, css):
        try:
            h = e.get_attribute("href")
            if h:
                out.append(h)
        except StaleElementReferenceException:
            continue
    return out


def harvest(driver, extract_fn, scroll_fn, patience=12, pause=1.6, hard_limit=5000, log=print):
    """extract_fn(driver) -> [handle...]; scroll_fn(driver) listeyi asagi kaydirir.
       Yeni kullanici gelmeyi durdurunca (patience tur ust uste) biter."""
    seen = set()
    stale = 0
    rnd = 0
    while stale < patience and len(seen) < hard_limit:
        rnd += 1
        for h in extract_fn(driver):
            if h:
                seen.add(h)
        before = len(seen)
        scroll_fn(driver)
        time.sleep(pause)
        for h in extract_fn(driver):
            if h:
                seen.add(h)
        stale = stale + 1 if len(seen) == before else 0
        log(f"   round {rnd:>3}: {len(seen):>5} users  (no-change rounds: {stale})")
    return sorted(seen, key=str.lower)


# --------------------------------------------------------------- instagram

def scroll_ig(driver):
    driver.execute_script("""
      const dlg = document.querySelector('div[role="dialog"]');
      if (!dlg) return false;
      let target = null;
      for (const el of dlg.querySelectorAll('*')) {
        const oy = getComputedStyle(el).overflowY;
        if (el.scrollHeight > el.clientHeight + 50 && (oy === 'auto' || oy === 'scroll')) {
          target = el; break;
        }
      }
      target = target || dlg;
      target.scrollTop = target.scrollHeight;
      return true;
    """)


def extract_ig(driver):
    return [clean_ig_handle(h) for h in _hrefs_in(driver, 'div[role="dialog"] a[href]')]


def open_ig_list(driver, username, which):  # which: "followers" | "following"
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    driver.get(f"https://www.instagram.com/{username}/{which}/")
    WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"]')))
    time.sleep(2.5)


def run_instagram(driver, username, patience, pause, log=print):
    log("\n[Instagram] collecting accounts you follow ...")
    open_ig_list(driver, username, "following")
    following = harvest(driver, extract_ig, scroll_ig, patience, pause, log=log)

    log("\n[Instagram] collecting your followers ...")
    open_ig_list(driver, username, "followers")
    followers = harvest(driver, extract_ig, scroll_ig, patience, pause, log=log)
    return following, followers


# --------------------------------------------------------------- twitter / x

def scroll_tw(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


def extract_tw(driver):
    hrefs = _hrefs_in(driver, '[data-testid="UserCell"] a[href]')
    if not hrefs:  # selektor degismisse genel main'e dus
        hrefs = _hrefs_in(driver, 'main a[href]')
    return [clean_tw_handle(h) for h in hrefs]


def open_tw_list(driver, username, which):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    driver.get(f"https://x.com/{username}/{which}")
    try:
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="UserCell"]')))
    except Exception:
        time.sleep(5)  # bos/yeni hesap olabilir
    time.sleep(2.5)


def run_twitter(driver, username, patience, pause, log=print):
    log("\n[X] collecting accounts you follow ...")
    open_tw_list(driver, username, "following")
    following = harvest(driver, extract_tw, scroll_tw, patience, pause, log=log)

    log("\n[X] collecting your followers ...")
    open_tw_list(driver, username, "followers")
    followers = harvest(driver, extract_tw, scroll_tw, patience, pause, log=log)
    return following, followers


# --------------------------------------------------------------- GUI-callable entry point

def collect(platform, username, profile_dir="./chrome-profile", patience=12, pause=1.6,
            wait_for_ready=None, log=print, on_browser_open=None):
    """Open browser, wait for the caller to confirm login, then harvest both lists.

    platform        : "instagram" | "twitter"
    wait_for_ready  : callable that blocks until the user has finished logging in.
                      In the CLI this is input(); in the GUI it is an Event.wait().
    on_browser_open : optional callback(driver) fired right after the browser opens
                      (so a GUI can enable its "I'm logged in" button).
    log             : message sink (defaults to print).

    Returns (following, followers) as sorted lists of handles.
    """
    if platform not in ("instagram", "twitter"):
        raise ValueError(f"unknown platform: {platform}")
    username = username.strip().lstrip("@")
    if not username:
        raise ValueError("username is empty")

    driver = build_driver(profile_dir)
    try:
        start = ("https://www.instagram.com/" if platform == "instagram"
                 else "https://x.com/home")
        driver.get(start)
        log("Browser opened. Log in (2FA / checkpoint included), then continue.")
        if on_browser_open:
            on_browser_open(driver)
        if wait_for_ready:
            wait_for_ready()

        runner = run_instagram if platform == "instagram" else run_twitter
        following, followers = runner(driver, username, patience, pause, log=log)
        return following, followers
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# --------------------------------------------------------------- cli

def save(names, path):
    Path(path).write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"[kayit] {path}  ({len(names)} kullanici)")


def main():
    ap = argparse.ArgumentParser(description="IG/Twitter takipci+takip listesi topla (Selenium).")
    ap.add_argument("platform", choices=["instagram", "twitter"])
    ap.add_argument("username", help="KENDI kullanici adin (@ olmadan)")
    ap.add_argument("--profile-dir", default="./chrome-profile",
                    help="Kalici Chrome profili (login burada saklanir)")
    ap.add_argument("--patience", type=int, default=12,
                    help="Kac tur ust uste yeni kullanici gelmezse dursun (default 12)")
    ap.add_argument("--pause", type=float, default=1.6,
                    help="Her scroll sonrasi bekleme saniyesi (default 1.6)")
    ap.add_argument("--prefix", default=None, help="Cikti dosya oneki (default: platform)")
    args = ap.parse_args()

    prefix = args.prefix or args.platform

    def wait_for_ready():
        print("\n" + "=" * 60)
        print(" LOG IN in the opened browser (2FA / checkpoint included).")
        print(" Once you see the home page, come back here and press ENTER.")
        print("=" * 60)
        input(" > press ENTER when ready... ")

    following, followers = collect(
        args.platform, args.username,
        profile_dir=args.profile_dir, patience=args.patience, pause=args.pause,
        wait_for_ready=wait_for_ready,
    )

    save(following, f"{prefix}_following.txt")
    save(followers, f"{prefix}_followers.txt")

    print("\nDone. Now compare:")
    print(f"  python compare.py --following-list {prefix}_following.txt "
          f"--followers-list {prefix}_followers.txt --platform {args.platform} --save result_{prefix}")


if __name__ == "__main__":
    main()
