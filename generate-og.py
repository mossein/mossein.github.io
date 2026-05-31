#!/usr/bin/env python3
"""
generate-og.py — build a branded social-share image (Open Graph card) per blog post.

For each blog-post-*.html it reads the post's title and renders a 1200x630 PNG to
og/<post>.png with the title set in Fraunces on a clean background, then points
that post's og:image / twitter:image / schema image at its own card.

Run:  python3 generate-og.py
Requires Pillow and fonts/Fraunces.ttf (the variable Fraunces font).
The non-post pages keep the shared og.png.
"""

import glob
import os
import re
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
MARGIN = 96
BG = (250, 248, 245)        # warm paper white
INK = (26, 26, 26)
MUTED = (150, 148, 144)
FOOT = (92, 90, 86)
ACCENT = (0, 102, 204)      # site link blue
FONT_PATH = "fonts/Fraunces.ttf"
META_FONT = "/System/Library/Fonts/Helvetica.ttc"
OUT_DIR = "og"


def make_title_font(size, wght=560):
    f = ImageFont.truetype(FONT_PATH, size)
    try:
        vals = []
        for a in f.get_variation_axes():
            name = a["name"]
            name = name.decode() if isinstance(name, bytes) else name
            n = name.lower()
            if "optical" in n or "opsz" in n:
                vals.append(a["maximum"])           # display optical size
            elif "weight" in n or "wght" in n:
                vals.append(max(a["minimum"], min(a["maximum"], wght)))
            else:
                vals.append(a["default"])           # softness / wonky -> default
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f


def meta_font(size):
    try:
        return ImageFont.truetype(META_FONT, size)
    except Exception:
        return ImageFont.load_default()


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def og_title(html):
    m = re.search(r'property="og:title"\s+content="([^"]+)"', html)
    if not m:
        m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else None


def render_card(title, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    max_w = W - 2 * MARGIN

    # shrink the title until it fits ~4 lines within the body area
    size = 90
    while size > 42:
        font = make_title_font(size)
        lines = wrap(d, title, font, max_w)
        line_h = size * 1.13
        if len(lines) <= 4 and line_h * len(lines) <= H - 300:
            break
        size -= 4
    line_h = size * 1.13

    # kicker (top-left)
    kf = meta_font(28)
    d.text((MARGIN, MARGIN), "mohammad jafari", font=kf, fill=MUTED)

    # title block, vertically centered in the middle band
    block_h = line_h * len(lines)
    top = max(MARGIN + 70, (H - block_h) / 2 - 14)
    y = top
    for ln in lines:
        d.text((MARGIN, y), ln, font=font, fill=INK)
        y += line_h

    # footer: accent dot + domain (bottom-left)
    ff = meta_font(30)
    fy = H - MARGIN - 8
    r = 7
    d.ellipse([MARGIN, fy + 9, MARGIN + 2 * r, fy + 9 + 2 * r], fill=ACCENT)
    d.text((MARGIN + 2 * r + 14, fy), "mohammad.page", font=ff, fill=FOOT)

    img.save(out_path, "PNG", optimize=True)


def main():
    if not os.path.exists(FONT_PATH):
        print("missing %s — see the curl step in the README" % FONT_PATH)
        return
    os.makedirs(OUT_DIR, exist_ok=True)

    posts = sorted(glob.glob("blog-post-*.html"))
    for post in posts:
        stem = os.path.splitext(os.path.basename(post))[0]
        html = open(post).read()
        title = og_title(html)
        if not title:
            print("skip %s (no title)" % post)
            continue

        out_path = os.path.join(OUT_DIR, stem + ".png")
        render_card(title, out_path)

        # point this post's social image at its own card (idempotent)
        card_url = "https://mohammad.page/%s/%s.png" % (OUT_DIR, stem)
        new_html = html.replace("https://mohammad.page/og.png", card_url)
        if new_html != html:
            open(post, "w").write(new_html)

        print("ok  %s  ->  %s   \"%s\"" % (post, out_path, title))

    print("\ngenerated %d card(s)." % len(posts))


if __name__ == "__main__":
    main()
