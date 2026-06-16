#!/usr/bin/env python3
"""
make_example_image.py — generate fake "expected result" screenshots for the
README (one per platform). Uses made-up usernames only (no real accounts).
Mirrors the app's dark theme and result screen.

    python make_example_image.py
        -> assets/example-result.png            (Instagram)
        -> assets/example-result-twitter.png    (Twitter / X)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

# palette (matches app.py)
WIN_BG = "#0f1320"
CARD = "#1a2030"
CARD_2 = "#222a3d"
INK = "#eef1f7"
SUB = "#9aa4ba"
LINE = "#2c3550"
IG = "#e1306c"
TW = "#1d9bf0"
NFB = "#ff7a90"
YDF = "#5ec9ff"

W, H = 980, 620

PLATFORMS = {
    "instagram": {
        "title": "Instagram",
        "color": IG,
        "out": "example-result.png",
        "save_dir": "result_instagram/",
        "log_tag": "[Instagram]",
        "not_following_back": [
            "late_night_dev", "coffee.and.code", "marina_sky", "tom.builds",
            "pixel_pusher", "the_wanderer22", "greenleaf.studio", "nova_designs",
            "max_on_film", "quiet_garden",
        ],
        "you_dont_follow_back": [
            "daily_mtb", "promo_deals_xx", "artsy_anna", "gym_bro_99",
            "newsbot_live", "oldfriend_k", "travel_with_me", "cat_photos_daily",
            "bookworm_em", "retro_arcade", "the_food_log", "weekend_hiker",
        ],
        "counts": (318, 412, 306),
    },
    "twitter": {
        "title": "Twitter / X",
        "color": TW,
        "out": "example-result-twitter.png",
        "save_dir": "result_twitter/",
        "log_tag": "[X]",
        "not_following_back": [
            "devlogdaily", "synthwave_fm", "ada_writes", "buildinpublic_j",
            "marketmoves", "cold_brew_co", "indiehacker_t", "mapsandtrails",
        ],
        "you_dont_follow_back": [
            "crypto_alerts_", "viral_threads", "the_meme_desk", "sportscenter_x",
            "newsnow_live", "dealhunter99", "random_reply", "podcast_clipz",
            "techbro_takes", "lurker_no7", "weather_bot_", "quote_machine",
            "gm_every_day", "ai_paperbot",
        ],
        "counts": (842, 197, 168),
    },
}


def font(size, bold=False, mono=False):
    try:
        if mono:
            return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size)
        path = ("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
                else "/System/Library/Fonts/Supplemental/Arial.ttf")
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def ig_logo(d, x, y, s, color):
    pad = s * 0.13
    w = max(2, int(s * 0.09))
    d.rounded_rectangle([x + pad, y + pad, x + s - pad, y + s - pad],
                        radius=s * 0.24, outline=color, width=w)
    cx, cy, r = x + s / 2, y + s / 2, s * 0.20
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)
    dr = s * 0.05
    dx, dy = x + s - pad - s * 0.11, y + pad + s * 0.11
    d.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=color)


def x_logo(d, x, y, s, color):
    pad = s * 0.20
    w = max(3, int(s * 0.16))
    d.line([x + pad, y + pad, x + s - pad, y + s - pad], fill=color, width=w)
    d.line([x + s - pad, y + pad, x + pad, y + s - pad], fill=color, width=w)


def column(d, x, y, w, h, title, accent, handles):
    d.rounded_rectangle([x, y, x + w, y + 34], radius=8, fill=accent)
    d.rectangle([x, y + 20, x + w, y + 34], fill=accent)
    d.text((x + 12, y + 8), title, font=font(15, bold=True), fill="#10141f")
    by = y + 34
    d.rectangle([x, by, x + w, y + h], fill=CARD_2)
    fm = font(15, mono=True)
    for i, u in enumerate(handles):
        ty = by + 8 + i * 26
        if ty > y + h - 26:
            break
        d.text((x + 12, ty), "@" + u, font=fm, fill=INK)


def generate(platform):
    cfg = PLATFORMS[platform]
    nfb, ydf = cfg["not_following_back"], cfg["you_dont_follow_back"]
    following, followers, mutuals = cfg["counts"]

    img = Image.new("RGB", (W, H), WIN_BG)
    d = ImageDraw.Draw(img)

    # top bar
    d.text((20, 22), "←  Back", font=font(14), fill=SUB)
    if platform == "instagram":
        ig_logo(d, 96, 16, 26, cfg["color"])
    else:
        x_logo(d, 96, 16, 26, cfg["color"])
    d.text((130, 18), cfg["title"], font=font(18, bold=True), fill=INK)
    d.text((W - 70, 22), "Done", font=font(13, bold=True), fill=SUB)

    # instruction card
    d.rounded_rectangle([18, 56, W - 18, 150], radius=12, fill=CARD)
    d.text((36, 72), "Result", font=font(20, bold=True), fill=INK)
    d.text((36, 108), f"Saved to {cfg['save_dir']}.  Press Back to start over.",
           font=font(14), fill=SUB)

    # results + log
    top, col_w = 174, 250
    h = H - top - 24
    column(d, 18, top, col_w, h, f"Don't follow you back ({len(nfb)})", NFB, nfb)
    column(d, 18 + col_w + 12, top, col_w, h,
           f"You don't follow back ({len(ydf)})", YDF, ydf)

    lx = 18 + (col_w + 12) * 2
    lw = W - 18 - lx
    d.text((lx, top - 22), "Log", font=font(13), fill=SUB)
    d.rounded_rectangle([lx, top, lx + lw, top + h], radius=8, fill=CARD_2,
                        outline=LINE, width=1)
    tag = cfg["log_tag"]
    log_lines = [
        "Browser opened. Log in.",
        f"{tag} collecting your",
        "  followers ...",
        "   round   1:    31 users",
        "   round   2:    74 users",
        "   round   3:   120 users",
        "   ...",
        f"   → {followers} followers collected.",
        f"{tag} collecting accounts",
        "  you follow ...",
        f"   → {following} following collected.",
        "",
        f"Done. Following {following},",
        f"followers {followers}, mutuals {mutuals}.",
    ]
    fm = font(12, mono=True)
    for i, ln in enumerate(log_lines):
        d.text((lx + 10, top + 10 + i * 18), ln, font=fm, fill=SUB)

    out = ASSETS / cfg["out"]
    img.save(out)
    print(f"wrote {out}  ({img.width}x{img.height})")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for platform in PLATFORMS:
        generate(platform)


if __name__ == "__main__":
    main()
