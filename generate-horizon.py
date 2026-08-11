#!/usr/bin/env python3
"""
generate-horizon.py — regenerate the horizon SVG on the homepage.

The horizon is the glow hiding under the end of index.html: a row of heavily
blurred bars that all paint the same vertical gradient, arranged so their
heights trace the toronto skyline (CN Tower spike and all). The blur melts
them into one soft field of light — the same trick as Dia Browser's footer
gradient, with our own skyline and palettes.

Workflow:
    1. Tweak BARS / OVERLAP / BLUR below
    2. Run:  python3 generate-horizon.py
    3. Paste the printed <svg> over the one inside <div class="horizon"> in
       index.html

Colors are NOT here — each <stop> carries a class (hg-0 … hg-7) and the
palettes live in styles.css, one set per theme, so the glow re-colors with
the theme toggle without touching the markup. The overscroll behavior
(pull past the bottom of the page, spring back on release) lives in nav.js.
"""

VBW, VBH = 1271, 599
PEAK = 0.98  # global height scale so the tower kisses the top edge

# (relative width, height fraction) west -> east; widths sum to 1.0.
# neighbour deltas stay small (<= ~0.14) so the gradient bands connect into
# smooth arcs instead of disconnected blobs — the CN Tower is the one
# deliberate jump.
BARS = [
    (0.095, 0.30),
    (0.085, 0.44),
    (0.075, 0.56),
    (0.048, 0.94),  # CN Tower
    (0.075, 0.52),  # Rogers Centre dip
    (0.085, 0.64),
    (0.082, 0.78),  # financial district cluster
    (0.078, 0.70),
    (0.085, 0.60),
    (0.095, 0.48),
    (0.098, 0.38),
    (0.099, 0.28),
]
assert abs(sum(w for w, _ in BARS) - 1.0) < 1e-9

OVERLAP = 1.4       # bars bleed into their neighbour so the blur melts them
TOWER_OVERLAP = 1.3 # the spike still merges at its base
BLUR = 21           # feGaussianBlur stdDeviation, in viewBox units

# gradient stop offsets, bottom -> top; colors come from styles.css classes
STOPS = ["0", "0.14", "0.26", "0.42", "0.58", "0.7", "0.82", "1"]


def f(n):
    s = f"{n:.1f}"
    return s[:-2] if s.endswith(".0") else s


def main():
    rects = []
    x = 0.0
    for w, hf in BARS:
        bw = w * VBW
        h = hf * PEAK * VBH
        ov = TOWER_OVERLAP if hf > 0.9 else OVERLAP
        rects.append(
            f'<g filter="url(#horizon-blur)"><rect x="{f(x - bw * (ov - 1) / 2)}" '
            f'y="{f(VBH - h)}" width="{f(bw * ov)}" height="{f(h)}" '
            f'fill="url(#horizon-grad)"/></g>'
        )
        x += bw

    stops = "".join(
        f'<stop offset="{o}" class="hg-{i}"/>' for i, o in enumerate(STOPS)
    )

    print(
        f'<svg viewBox="0 0 {VBW} {VBH}" preserveAspectRatio="none" '
        'xmlns="http://www.w3.org/2000/svg" focusable="false">'
        '<defs>'
        f'<linearGradient id="horizon-grad" x1="0" y1="1" x2="0" y2="0">{stops}</linearGradient>'
        # the region is generous on x: it's per-rect, and the skinny CN Tower
        # bar would otherwise clip the blur into a hard vertical edge
        '<filter id="horizon-blur" x="-100%" y="-50%" width="300%" height="200%">'
        f'<feGaussianBlur stdDeviation="{BLUR}"/></filter>'
        '</defs>'
        + "".join(rects)
        + "</svg>"
    )


if __name__ == "__main__":
    main()
