#!/usr/bin/env python3
"""
Karsilikli takip karsilastirma araci (Instagram / Twitter / genel).

Iki listeyi karsilastirir:
  - following : senin takip ettiklerin
  - followers : seni takip edenler

Cikti:
  1) Sen takip ediyorsun ama o GERI takip etmiyor   (not_following_back)
  2) O seni takip ediyor ama sen geri takip etmiyorsun (you_dont_follow_back)
  3) Karsilikli (mutuals) -> sadece sayi

Veri kaynaklari:
  * Instagram resmi veri indirme (JSON): following.json + followers_1.json (followers_2.json ...)
  * Duz metin listesi: her satirda bir kullanici adi (Twitter ya da baska bir yontemle topladiklarin)

Hicbir ucuncu parti kutuphane gerektirmez (sadece Python stdlib).
"""

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------- parsers

def _usernames_from_ig_obj(data):
    """Instagram export'un iki bicimini de destekler:
       - kok seviyede liste            -> followers_1.json
       - relationships_* anahtarli dict -> following.json
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
    """case-insensitive eslestirme: lowercase -> ilk gorulen orijinal isim."""
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
    title = f" KARSILASTIRMA{(' - ' + platform) if platform else ''} "
    print(bar)
    print(title.center(58, "="))
    print(bar)
    print(f"Takip ettigin   : {r['following_count']}")
    print(f"Seni takip eden : {r['followers_count']}")
    print(f"Karsilikli      : {len(r['mutuals'])}")
    print()

    nfb = r["not_following_back"]
    print(f"[X] Sen takip ediyorsun, o GERI TAKIP ETMIYOR  ({len(nfb)})")
    print("-" * 58)
    print("\n".join(f"  @{u}" for u in nfb) if nfb else "  (yok)")
    print()

    ydf = r["you_dont_follow_back"]
    print(f"[+] Seni takip ediyor, SEN GERI TAKIP ETMIYORSUN  ({len(ydf)})")
    print("-" * 58)
    print("\n".join(f"  @{u}" for u in ydf) if ydf else "  (yok)")
    print()


def save_lists(r, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "geri_takip_etmeyenler.txt").write_text(
        "\n".join(r["not_following_back"]) + "\n", encoding="utf-8")
    (out / "sen_takip_etmediklerin.txt").write_text(
        "\n".join(r["you_dont_follow_back"]) + "\n", encoding="utf-8")
    print(f"[kayit] {out}/geri_takip_etmeyenler.txt")
    print(f"[kayit] {out}/sen_takip_etmediklerin.txt")


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
        description="Karsilikli olmayan takipleri bul (Instagram/Twitter/genel).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--ig-dir", help="Instagram export'taki .../followers_and_following klasoru (dosyalari otomatik bulur)")
    ap.add_argument("--following", help="following.json yolu (Instagram)")
    ap.add_argument("--followers", nargs="+", help="followers_1.json (ve varsa followers_2.json ...) yollari")
    ap.add_argument("--following-list", help="Takip ettiklerin: her satirda bir kullanici adi (duz metin)")
    ap.add_argument("--followers-list", help="Seni takip edenler: her satirda bir kullanici adi (duz metin)")
    ap.add_argument("--platform", default="", help="Rapor basligi etiketi (Instagram / Twitter)")
    ap.add_argument("--save", metavar="DIR", help="Sonuclari .txt olarak bu klasore kaydet")
    args = ap.parse_args()

    following_names = follower_names = None

    if args.ig_dir:
        ff_following, ff_followers = autodetect_instagram(args.ig_dir)
        if not ff_following or not ff_followers:
            sys.exit("Klasorde following.json / followers_*.json bulunamadi.")
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
        sys.exit("\nHata: ya --ig-dir, ya (--following + --followers), "
                 "ya da (--following-list + --followers-list) ver.")

    result = compare(following_names, follower_names)
    print_report(result, args.platform)
    if args.save:
        save_lists(result, args.save)


if __name__ == "__main__":
    main()
