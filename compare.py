#!/usr/bin/env python3
"""
Mutual-follow comparison tool (Instagram / Twitter / generic).

Compares two lists:
  - following : the accounts you follow
  - followers : the accounts that follow you

Output:
  1) You follow them but they DON'T follow you back   (not_following_back)
  2) They follow you but you DON'T follow them back    (you_dont_follow_back)
  3) Mutuals -> count only

Data sources:
  * Instagram official data download (JSON): following.json + followers_1.json (followers_2.json ...)
  * Plain text list: one username per line (Twitter, or anything you collected another way)

Requires no third-party libraries (Python stdlib only).
"""

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------- parsers

def _usernames_from_ig_obj(data):
    """Supports both shapes of the Instagram export:
       - a list at the root level           -> followers_1.json
       - a dict keyed by relationships_*     -> following.json
    """
    if isinstance(data, dict):
        records = next((v for v in data.values() if isinstance(v, list)), [])
    elif isinstance(data, list):
        records = data
    else:
        records = []

    names = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        for item in rec.get("string_list_data", []):
            val = item.get("value")
            if not val and item.get("href"):
                val = item["href"].rstrip("/").split("/")[-1]
            if val:
                names.append(val.strip())
    return names


def load_instagram_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return _usernames_from_ig_obj(json.load(f))


def load_text_list(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip().lstrip("@")
            if name and not name.startswith("#"):
                out.append(name)
    return out


# ---------------------------------------------------------------- core

def _index(names):
    """case-insensitive matching: lowercase -> first-seen original spelling."""
    mapping = {}
    for n in names:
        mapping.setdefault(n.lower(), n)
    return mapping


def compare(following_names, follower_names):
    following = _index(following_names)
    followers = _index(follower_names)

    f, fo = set(following), set(followers)

    return {
        "following_count": len(f),
        "followers_count": len(fo),
        "not_following_back": sorted((following[k] for k in f - fo), key=str.lower),
        "you_dont_follow_back": sorted((followers[k] for k in fo - f), key=str.lower),
        "mutuals": sorted((following[k] for k in f & fo), key=str.lower),
    }


# ---------------------------------------------------------------- output

def print_report(r, platform=""):
    bar = "=" * 58
    title = f" COMPARISON{(' - ' + platform) if platform else ''} "
    print(bar)
    print(title.center(58, "="))
    print(bar)
    print(f"Following : {r['following_count']}")
    print(f"Followers : {r['followers_count']}")
    print(f"Mutuals   : {len(r['mutuals'])}")
    print()

    nfb = r["not_following_back"]
    print(f"[X] You follow them, they DON'T follow you back  ({len(nfb)})")
    print("-" * 58)
    print("\n".join(f"  @{u}" for u in nfb) if nfb else "  (none)")
    print()

    ydf = r["you_dont_follow_back"]
    print(f"[+] They follow you, you DON'T follow them back  ({len(ydf)})")
    print("-" * 58)
    print("\n".join(f"  @{u}" for u in ydf) if ydf else "  (none)")
    print()


def save_lists(r, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "not_following_back.txt").write_text(
        "\n".join(r["not_following_back"]) + "\n", encoding="utf-8")
    (out / "you_dont_follow_back.txt").write_text(
        "\n".join(r["you_dont_follow_back"]) + "\n", encoding="utf-8")
    print(f"[saved] {out}/not_following_back.txt")
    print(f"[saved] {out}/you_dont_follow_back.txt")


# ---------------------------------------------------------------- ig autodetect

def autodetect_instagram(dir_path):
    d = Path(dir_path)
    following = d / "following.json"
    following = following if following.exists() else None
    followers = sorted(d.glob("followers_*.json")) or sorted(d.glob("followers.json"))
    return following, followers


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(
        description="Find non-mutual follows (Instagram/Twitter/generic).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--ig-dir", help="The .../followers_and_following folder from the Instagram export (auto-detects files)")
    ap.add_argument("--following", help="Path to following.json (Instagram)")
    ap.add_argument("--followers", nargs="+", help="Path(s) to followers_1.json (and followers_2.json ... if present)")
    ap.add_argument("--following-list", help="Accounts you follow: one username per line (plain text)")
    ap.add_argument("--followers-list", help="Accounts that follow you: one username per line (plain text)")
    ap.add_argument("--platform", default="", help="Report title label (Instagram / Twitter)")
    ap.add_argument("--save", metavar="DIR", help="Save results as .txt into this folder")
    args = ap.parse_args()

    following_names = follower_names = None

    if args.ig_dir:
        ff_following, ff_followers = autodetect_instagram(args.ig_dir)
        if not ff_following or not ff_followers:
            sys.exit("Could not find following.json / followers_*.json in the folder.")
        following_names = load_instagram_json(ff_following)
        follower_names = [u for ff in ff_followers for u in load_instagram_json(ff)]
        args.platform = args.platform or "Instagram"

    elif args.following and args.followers:
        following_names = load_instagram_json(args.following)
        follower_names = [u for ff in args.followers for u in load_instagram_json(ff)]
        args.platform = args.platform or "Instagram"

    elif args.following_list and args.followers_list:
        following_names = load_text_list(args.following_list)
        follower_names = load_text_list(args.followers_list)

    else:
        ap.print_help()
        sys.exit("\nError: provide either --ig-dir, or (--following + --followers), "
                 "or (--following-list + --followers-list).")

    result = compare(following_names, follower_names)
    print_report(result, args.platform)
    if args.save:
        save_lists(result, args.save)


if __name__ == "__main__":
    main()
