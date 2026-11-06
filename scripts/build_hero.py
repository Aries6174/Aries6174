"""Builds assets/hero.svg: a dragon curve that folds itself, one fold at a time.

The Heighway dragon is what you get by folding a strip of paper in half over and over,
then opening every fold to a right angle. Each fold takes the whole curve so far and adds
a copy of it, turned 90 degrees around the curve's end. That's exactly what this animates:
for fold k, the curve from fold k-1 stays still while a copy of it swings out.

Only two paths are visible at any moment, so it stays light even with thousands of lines.
Everything is plain SVG with SMIL animation, which GitHub shows in a README image.

Run from the repo root:  python scripts/build_hero.py
"""

import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
OUT = ROOT / "assets" / "hero.svg"

W, H = 1200, 440
# Where the curve is drawn, right of the text. Lines keep the same width at any zoom,
# which needs vector-effect on each shape, as groups don't pass it down.
STAGE = (470, 36, 700, 368)
FOLDS = 12

GOLD = "#f0bb66"
BRIGHT = "#ffe1a8"
PALE = "#f4eee2"
SOFT = "#b9ad9a"
MUTED = "#7d705d"
INK = "#0b0805"
LINE = "#5a4325"

# Seconds for each fold, a pause on the finished dragon, and a fade before it starts again.
def fold_time(k):
    return 0.55 if k <= 4 else 0.8 if k <= 8 else 1.05


HOLD = 3.2
FADE = 0.8


def dragon(folds):
    """Points of the curve after each fold. Fold k adds the previous curve turned about its end."""
    curves = [[(0, 0), (1, 0)]]
    for _ in range(folds):
        points = curves[-1]
        ex, ey = points[-1]
        # Turn every point 90 degrees about the end, then walk back along the copy.
        turned = [(ex + (y - ey), ey - (x - ex)) for x, y in points]
        curves.append(points + turned[-2::-1])
    return curves


def path_data(points):
    """Unit steps written as short relative moves: h and v with a length of one."""
    out = [f"M{points[0][0]} {points[0][1]}"]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        out.append(f"h{x1 - x0}" if y1 == y0 else f"v{y1 - y0}")
    return "".join(out)


def camera(points):
    """The scale and offset that fit these points in the stage."""
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    sx, sy, sw, sh = STAGE
    width = max(xs) - min(xs) or 1
    height = max(ys) - min(ys) or 1
    # Room to spare, as a fold swings wider than where it starts or ends.
    scale = min(sw * 0.74 / width, sh * 0.74 / height, 80)
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2
    return scale, sx + sw / 2 - cx * scale, sy + sh / 2 - cy * scale


def font_face(family, path, text):
    font = TTFont(path)
    options = subset.Options()
    options.flavor = "woff2"
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    data = io.BytesIO()
    font.flavor = "woff2"
    font.save(data)
    encoded = base64.b64encode(data.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{encoded}) format('woff2');}}"


def build():
    curves = dragon(FOLDS)
    starts = []
    t = 0.0
    for k in range(1, FOLDS + 1):
        starts.append(t)
        t += fold_time(k)
    folded_at = t
    total = folded_at + HOLD + FADE

    def at(seconds):
        return f"{min(max(seconds / total, 0), 1):.5f}"

    layers = []
    for k in range(1, FOLDS + 1):
        base = curves[k - 1]
        begin = starts[k - 1]
        end = begin + fold_time(k)
        last = k == FOLDS
        hide = total if last else end
        ex, ey = base[-1]
        s0, x0, y0 = camera(base)
        s1, x1, y1 = camera(curves[k])
        # Visible only for its own fold, except the last one, which stays for the pause.
        visible = (
            f'<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="0;{at(begin)};{at(hide)}" values="0;1;0"/>'
        )
        move = (
            f'<animateTransform attributeName="transform" type="translate" dur="{total:.2f}s" repeatCount="indefinite" '
            f'keyTimes="0;{at(begin)};{at(end)};1" values="{x0:.2f} {y0:.2f};{x0:.2f} {y0:.2f};{x1:.2f} {y1:.2f};{x1:.2f} {y1:.2f}" '
            f'calcMode="spline" keySplines="0 0 1 1;.45 0 .25 1;0 0 1 1"/>'
        )
        zoom = (
            f'<animateTransform attributeName="transform" type="scale" dur="{total:.2f}s" repeatCount="indefinite" '
            f'keyTimes="0;{at(begin)};{at(end)};1" values="{s0:.4f};{s0:.4f};{s1:.4f};{s1:.4f}" '
            f'calcMode="spline" keySplines="0 0 1 1;.45 0 .25 1;0 0 1 1"/>'
        )
        swing = (
            f'<animateTransform attributeName="transform" type="rotate" dur="{total:.2f}s" repeatCount="indefinite" '
            f'keyTimes="0;{at(begin)};{at(end)};1" values="0 {ex} {ey};0 {ex} {ey};-90 {ex} {ey};-90 {ex} {ey}" '
            f'calcMode="spline" keySplines="0 0 1 1;.45 0 .25 1;0 0 1 1"/>'
        )
        # The new half is brighter while it swings, then settles to gold.
        settle = (
            f'<animate attributeName="stroke" dur="{total:.2f}s" repeatCount="indefinite" '
            f'keyTimes="0;{at(begin)};{at(end)};1" values="{BRIGHT};{BRIGHT};{GOLD if last else BRIGHT};{GOLD if last else BRIGHT}"/>'
        )
        layers.append(
            f'<g opacity="0">{visible}<g>{move}<g>{zoom}'
            f'<path id="c{k}" d="{path_data(base)}" vector-effect="non-scaling-stroke"/>'
            f'<use href="#c{k}" stroke="{BRIGHT}" vector-effect="non-scaling-stroke">{swing}{settle}</use>'
            f"</g></g></g>"
        )

    counters = []
    for k in range(1, FOLDS + 1):
        begin = starts[k - 1]
        hide = total if k == FOLDS else starts[k]
        counters.append(
            f'<text x="56" y="214" font-family="Display" font-size="96" letter-spacing="4" fill="{PALE}" opacity="0">{k:02d}'
            f'<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="0;{at(begin)};{at(hide)}" values="0;1;0"/></text>'
        )
    segments = 2 ** FOLDS
    lines = {
        "prompt": "adrian@cosmic-archive ~ fold --times 12",
        "label": "FOLDS",
        "fact": "Fold a strip of paper in half 12 times,",
        "fact2": "open every fold to a right angle,",
        "fact3": f"and its {segments:,} edges draw a dragon.",
        "name": "HEIGHWAY DRAGON",
    }
    display = lines["label"] + lines["name"] + "".join(f"{k:02d}" for k in range(1, FOLDS + 1))
    body = lines["prompt"] + lines["fact"] + lines["fact2"] + lines["fact3"]
    styles = font_face("Display", FONTS / "Rajdhani-SemiBold.woff2", display) + font_face(
        "Body", FONTS / "Barlow-Regular.woff2", body
    )
    fade = (
        f'<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" '
        f'keyTimes="0;{at(folded_at + HOLD)};{at(total)};1" values="1;1;0;0"/>'
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="A gold Heighway dragon curve folding itself twelve times, beside a terminal prompt.">
<defs>
<style>{styles}text{{font-variant-ligatures:none}}</style>
<radialGradient id="glow" cx="72%" cy="48%" r="55%"><stop offset="0" stop-color="#3a2410"/><stop offset="1" stop-color="{INK}"/></radialGradient>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#glow)"/>
<g fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">
<g>{fade}{''.join(layers)}</g>
</g>
<text x="56" y="70" font-family="Body" font-size="17" fill="{MUTED}">{lines['prompt']}</text>
<text x="56" y="112" font-family="Display" font-size="18" letter-spacing="6" fill="{GOLD}">{lines['label']}</text>
{''.join(counters)}
<line x1="56" y1="246" x2="110" y2="246" stroke="{GOLD}"/>
<text font-family="Body" font-size="19" fill="{SOFT}"><tspan x="56" y="288">{lines['fact']}</tspan><tspan x="56" y="316">{lines['fact2']}</tspan><tspan x="56" y="344">{lines['fact3']}</tspan></text>
<text x="56" y="396" font-family="Display" font-size="15" letter-spacing="5" fill="{MUTED}">{lines['name']}</text>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{LINE}"/>
<path d="M1 30V1h29M{W - 1} {H - 30}V{H - 1}h-29" fill="none" stroke="{GOLD}" stroke-width="3"/>
</svg>
"""


def main():
    svg = build()
    OUT.write_text(svg, encoding="utf8")
    print(f"{OUT.relative_to(ROOT)}  {len(svg.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
