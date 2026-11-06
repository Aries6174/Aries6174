"""Builds assets/hero.svg: a dragon curve that folds itself, then becomes the letters AJS.

The Heighway dragon is what you get by folding a strip of paper in half over and over,
then opening every fold to a right angle. Each fold takes the whole curve so far and adds
a copy of it, turned 90 degrees around the curve's end. That's exactly what this animates:
for fold k, the curve from fold k-1 stays still while a copy of it swings out.

When the dragon is done, its single line flows into "AJS". The letters are drawn as one
line too: each is filled by a maze, and walking around the walls of a maze visits every
square once and comes back to the start. Both lines are given the same number of points,
so SVG can slide each point from its place in the dragon to its place in the letters.

After a pause on AJS, everything plays backward to the single line, and the cycle repeats.

Only two paths are visible at any moment, so it stays light even with thousands of lines.
Everything is plain SVG with SMIL animation, which GitHub shows in a README image.

Run from the repo root:  python scripts/build_hero.py
"""

import base64
import io
import math
import random
from collections import defaultdict
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

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

# Seconds for each fold. The cycle opens on a single line, folds, becomes AJS, holds,
# then plays the same way back, so it ends on the single line it started from.
def fold_time(k):
    return 0.55 if k <= 4 else 0.8 if k <= 8 else 1.05


START = 0.8
HOLD = 3.2
# A short pause on the finished dragon, then the time it takes to become the letters.
SETTLE = 1.0
MORPH = 2.8
WORD = "AJS"


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


def letter_cells(rows):
    """For each letter of WORD, the grid squares it covers, at a letter height of about `rows`."""
    font_file = TTFont(FONTS / "Rajdhani-SemiBold.woff2")
    font_file.flavor = None
    data = io.BytesIO()
    font_file.save(data)
    cell = 8
    font = ImageFont.truetype(io.BytesIO(data.getvalue()), rows * cell)
    letters = []
    for char in WORD:
        left, top, right, bottom = font.getbbox(char)
        image = Image.new("L", (right - left + 2 * cell, bottom - top + 2 * cell), 0)
        ImageDraw.Draw(image).text((cell - left, cell - top), char, font=font, fill=255)
        cols, lines = math.ceil(image.width / cell), math.ceil(image.height / cell)
        small = image.resize((cols, lines), Image.BOX)
        cells = {(x, y) for y in range(lines) for x in range(cols) if small.getpixel((x, y)) > 140}
        letters.append((largest_piece(cells), cols))
    return letters


def largest_piece(cells):
    """Keeps the biggest group of touching squares, so each letter is one connected shape."""
    best, left = set(), set(cells)
    while left:
        stack = [left.pop()]
        piece = set(stack)
        while stack:
            x, y = stack.pop()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in left:
                    left.remove(n)
                    piece.add(n)
                    stack.append(n)
        if len(piece) > len(best):
            best = piece
    return best


def maze_loop(cells, rand):
    """One closed line through every square, made by walking around the walls of a random maze.

    Each square is split into four smaller ones. Where the maze has a passage the line
    crosses into the next square; where it has a wall the line turns back. Every small
    square ends up with exactly two neighbours on the line, so it forms a single loop.
    """
    start = max(cells, key=lambda c: (c[1], -c[0]))
    passages, seen, stack = set(), {start}, [start]
    while stack:
        x, y = stack[-1]
        options = [n for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if n in cells and n not in seen]
        if not options:
            stack.pop()
            continue
        nxt = rand.choice(options)
        seen.add(nxt)
        passages.add(frozenset(((x, y), nxt)))
        stack.append(nxt)

    links = defaultdict(list)

    def link(a, b):
        links[a].append(b)
        links[b].append(a)

    for x, y in cells:
        X, Y = 2 * x, 2 * y
        open_to = {d: frozenset(((x, y), (x + dx, y + dy))) in passages for d, (dx, dy) in {"r": (1, 0), "l": (-1, 0), "d": (0, 1), "u": (0, -1)}.items()}
        if not open_to["u"]:
            link((X, Y), (X + 1, Y))
        if not open_to["d"]:
            link((X, Y + 1), (X + 1, Y + 1))
        if not open_to["l"]:
            link((X, Y), (X, Y + 1))
        if not open_to["r"]:
            link((X + 1, Y), (X + 1, Y + 1))
        else:
            link((X + 1, Y), (X + 2, Y))
            link((X + 1, Y + 1), (X + 2, Y + 1))
        if open_to["d"]:
            link((X, Y + 1), (X, Y + 2))
            link((X + 1, Y + 1), (X + 1, Y + 2))

    first = (2 * start[0], 2 * start[1] + 1)
    loop, previous, here = [first], None, first
    while True:
        a, b = links[here]
        nxt = b if a == previous else a
        if nxt == first:
            break
        loop.append(nxt)
        previous, here = here, nxt
    assert len(loop) == 4 * len(cells), "the maze line missed some squares"
    return loop + [first]


def word_line(budget, seed=6):
    """AJS as one line in stage pixels, with as many points as fit within `budget`."""
    rand = random.Random(seed)
    for rows in range(46, 8, -1):
        letters = letter_cells(rows)
        if sum(4 * len(cells) + 1 for cells, _ in letters) <= budget:
            break
    points, offset = [], 0
    for cells, cols in letters:
        points += [(offset * 2 + x, y) for x, y in maze_loop(cells, random.Random(rand.random()))]
        offset += cols + 2
    scale, dx, dy = camera(points)
    return [(x * scale + dx, y * scale + dy) for x, y in points]


def match_length(points, n):
    """Adds points along the segments, spread evenly, until there are exactly n."""
    extra = n - len(points)
    segments = len(points) - 1
    out = [points[0]]
    for i in range(segments):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        parts = 1 + (extra * (i + 1)) // segments - (extra * i) // segments
        for j in range(1, parts + 1):
            out.append((x0 + (x1 - x0) * j / parts, y0 + (y1 - y0) * j / parts))
    return out


def relative_path(points):
    """Whole-pixel relative moves. Two of these with the same length can be blended smoothly."""
    rounded = [(round(x), round(y)) for x, y in points]
    out = [f"M{rounded[0][0]} {rounded[0][1]}"]
    for (x0, y0), (x1, y1) in zip(rounded, rounded[1:]):
        out.append(f"l{x1 - x0} {y1 - y0}")
    return "".join(out)


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
    """The whole cycle plays forward to AJS, holds, then plays backward to a single line.

    Every animation is written once as a list of (seconds, value) moments up to the
    middle of the cycle. `mirror` adds the same moments in reverse after the middle,
    so the return trip is the forward trip played backward and the loop has no seam.
    """
    curves = dragon(FOLDS)
    starts, t = [], START
    for k in range(1, FOLDS + 1):
        starts.append(t)
        t += fold_time(k)
    folded_at = t
    morph_start = folded_at + SETTLE
    morph_end = morph_start + MORPH
    middle = morph_end + HOLD / 2
    total = 2 * middle

    def mirror(moments):
        """The moments, then the same moments backward from the end of the cycle."""
        back = [(total - seconds, value) for seconds, value in reversed(moments)]
        return moments + [m for m in back if m[0] > moments[-1][0]]

    def key_times(moments):
        return ";".join(f"{seconds / total:.5f}" for seconds, _ in moments)

    def eased(attribute, moments, kind=None):
        """Smooth movement between moments, as `animate` or `animateTransform`."""
        moments = mirror(moments)
        if moments[0][0] > 0:
            moments = [(0, moments[0][1])] + moments
        if moments[-1][0] < total:
            moments = moments + [(total, moments[-1][1])]
        tag = "animateTransform" if kind else "animate"
        kind_attr = f' type="{kind}"' if kind else ""
        splines = ";".join(".5 0 .5 1" for _ in moments[1:])
        return (
            f'<{tag} attributeName="{attribute}"{kind_attr} dur="{total:.2f}s" repeatCount="indefinite" '
            f'keyTimes="{key_times(moments)}" values="{";".join(str(v) for _, v in moments)}" '
            f'calcMode="spline" keySplines="{splines}"/>'
        )

    def shown(start, end):
        """Visible from start to end going forward, and for the same stretch coming back."""
        moments = [(0, 0)] if start > 0 else []
        if end >= total / 2:
            # Visible across the middle: one stretch, from start to its mirror.
            moments += [(start, 1), (total - start, 0)]
        else:
            moments += [(start, 1), (end, 0), (total - end, 1), (total - start, 0)]
        moments = [m for m in moments if m[0] < total]
        if moments[0][0] > 0:
            moments = [(0, 0)] + moments
        return (
            f'<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{key_times(moments)}" values="{";".join(str(v) for _, v in moments)}"/>'
        )

    layers = []
    for k in range(1, FOLDS + 1):
        base = curves[k - 1]
        begin = starts[k - 1]
        end = begin + fold_time(k)
        last = k == FOLDS
        ex, ey = base[-1]
        s0, x0, y0 = camera(base)
        s1, x1, y1 = camera(curves[k])
        # The first fold is visible from the very start, so the cycle opens on a single line.
        visible_from = 0 if k == 1 else begin
        visible_to = morph_start if last else end
        layers.append(
            f'<g opacity="0">{shown(visible_from, visible_to)}'
            f'<g>{eased("transform", [(begin, f"{x0:.2f} {y0:.2f}"), (end, f"{x1:.2f} {y1:.2f}")], "translate")}'
            f'<g>{eased("transform", [(begin, f"{s0:.4f}"), (end, f"{s1:.4f}")], "scale")}'
            f'<path id="c{k}" d="{path_data(base)}" vector-effect="non-scaling-stroke"/>'
            f'<use href="#c{k}" stroke="{BRIGHT}" vector-effect="non-scaling-stroke">'
            f'{eased("transform", [(begin, f"0 {ex} {ey}"), (end, f"-90 {ex} {ey}")], "rotate")}'
            f'{eased("stroke", [(begin, BRIGHT), (end, GOLD if last else BRIGHT)])}'
            f"</use></g></g></g>"
        )

    # The finished dragon in stage pixels, and AJS with the same number of points.
    final = curves[FOLDS]
    fs, fx, fy = camera(final)
    dragon_line = [(x * fs + fx, y * fs + fy) for x, y in final]
    letters_line = match_length(word_line(len(dragon_line)), len(dragon_line))
    start_d, end_d = relative_path(dragon_line), relative_path(letters_line)
    layers.append(
        f'<path d="{start_d}" opacity="0">{shown(morph_start, middle)}'
        f'{eased("d", [(morph_start, start_d), (morph_end, end_d)])}'
        f'{eased("stroke", [(morph_start, BRIGHT), (morph_end, GOLD)])}'
        f"</path>"
    )

    counters = []
    for k in range(1, FOLDS + 1):
        begin = 0 if k == 1 else starts[k - 1]
        hide = middle if k == FOLDS else starts[k]
        counters.append(
            f'<text x="56" y="214" font-family="Display" font-size="96" letter-spacing="4" fill="{PALE}" opacity="0">{k:02d}'
            f"{shown(begin, hide)}</text>"
        )

    def crossfade(seconds, before, after):
        """Two copies of a piece of text that swap at a moment, and swap back on the return."""
        out_moments = [(seconds, 1), (seconds + 0.6, 0)]
        in_moments = [(seconds, 0), (seconds + 0.6, 1)]
        first = before.replace("<text ", '<text opacity="1" ', 1).replace("</text>", eased("opacity", out_moments) + "</text>")
        second = after.replace("<text ", '<text opacity="0" ', 1).replace("</text>", eased("opacity", in_moments) + "</text>")
        return first + second

    segments = 2 ** FOLDS
    lines = {
        "prompt": "adrian@cosmic-archive ~ fold --times 12",
        "label": "FOLDS",
        "fact": "Fold a strip of paper in half 12 times,",
        "fact2": "open every fold to a right angle,",
        "fact3": f"and its {segments:,} edges draw a dragon.",
        "fact3b": "then the same line spells my initials.",
        "name": "HEIGHWAY DRAGON",
        "nameb": "ADRIAN JOEL JASPA",
    }
    display = lines["label"] + lines["name"] + lines["nameb"] + "".join(f"{k:02d}" for k in range(1, FOLDS + 1))
    body = lines["prompt"] + lines["fact"] + lines["fact2"] + lines["fact3"] + lines["fact3b"]
    styles = font_face("Display", FONTS / "Rajdhani-SemiBold.woff2", display) + font_face(
        "Body", FONTS / "Barlow-Regular.woff2", body
    )
    fact3 = crossfade(
        morph_start,
        f'<text x="56" y="344" font-family="Body" font-size="19" fill="{SOFT}">{lines["fact3"]}</text>',
        f'<text x="56" y="344" font-family="Body" font-size="19" fill="{SOFT}">{lines["fact3b"]}</text>',
    )
    name = crossfade(
        morph_end - 0.6,
        f'<text x="56" y="396" font-family="Display" font-size="15" letter-spacing="5" fill="{MUTED}">{lines["name"]}</text>',
        f'<text x="56" y="396" font-family="Display" font-size="15" letter-spacing="5" fill="{GOLD}">{lines["nameb"]}</text>',
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="A gold Heighway dragon curve folds itself twelve times and its single line flows into the letters AJS, then it all unwinds back to one line.">
<defs>
<style>{styles}text{{font-variant-ligatures:none}}</style>
<radialGradient id="glow" cx="72%" cy="48%" r="55%"><stop offset="0" stop-color="#3a2410"/><stop offset="1" stop-color="{INK}"/></radialGradient>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#glow)"/>
<g fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">
{''.join(layers)}
</g>
<text x="56" y="70" font-family="Body" font-size="17" fill="{MUTED}">{lines['prompt']}</text>
<text x="56" y="112" font-family="Display" font-size="18" letter-spacing="6" fill="{GOLD}">{lines['label']}</text>
{''.join(counters)}
<line x1="56" y1="246" x2="110" y2="246" stroke="{GOLD}"/>
<text font-family="Body" font-size="19" fill="{SOFT}"><tspan x="56" y="288">{lines['fact']}</tspan><tspan x="56" y="316">{lines['fact2']}</tspan></text>
{fact3}
{name}
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
