"""Builds the project cards in assets/cards from assets/source and assets/fonts.

GitHub shows README images through a proxy that blocks outside files, so each card is a
single SVG with its picture and fonts embedded. The fonts are cut down to the letters the
card uses, which keeps every card small.

Run from the repo root:  python scripts/build_cards.py
Needs:                   pip install -r scripts/requirements.txt
"""

import base64
import io
import random
from html import escape

from PIL import Image, ImageOps, ImageStat

from svgkit import BRIGHT, FONTS, ROOT, font_face

SOURCE = ROOT / "assets" / "source"
OUT = ROOT / "assets" / "cards"

W, H = 840, 520
PICTURE_H = 330

GOLD = "#f0bb66"
PALE = "#f4eee2"
SOFT = "#b9ad9a"
INK = "#0b0805"
LINE = "#5a4325"

CARDS = [
    {
        "file": "adrian-js",
        "number": "01",
        "title": "ADRIAN.JS",
        "tagline": "My portfolio: five 3D worlds you can explore",
        "tags": ["Next.js", "Three.js", "TypeScript"],
        "picture": "portfolio.jpg",
    },
    {
        "file": "codewall",
        "number": "02",
        "title": "Codewall",
        "tagline": "A code editor that types by itself",
        "tags": ["Next.js", "TypeScript", "Tailwind CSS"],
        "picture": "codewall.jpg",
    },
    {
        "file": "taskflow",
        "number": "03",
        "title": "TaskFlow",
        "tagline": "A full-stack task manager, fully tested",
        "tags": ["Next.js", "PostgreSQL", "Playwright"],
        "picture": "taskflow.jpg",
    },
    {
        "file": "up-visions",
        "number": "04",
        "title": "UP: Visions",
        "tagline": "My thesis: an educational visual novel",
        "tags": ["Ren'Py", "Python", "Game design"],
        "picture": None,
    },
]


def picture(name: str) -> str:
    """The screenshot, cropped to the picture area at twice its display size."""
    image = Image.open(SOURCE / name).convert("RGB")
    target = W / PICTURE_H
    if image.width / image.height > target:
        width = round(image.height * target)
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    else:
        height = round(image.width / target)
        image = image.crop((0, 0, image.width, height))
    image = image.resize((W * 2, PICTURE_H * 2), Image.LANCZOS)
    # Light screenshots are recoloured in the cards' dark gold, so the set looks like one family.
    if sum(ImageStat.Stat(image).mean) / 3 > 140:
        image = ImageOps.colorize(ImageOps.invert(ImageOps.grayscale(image)), black="#0b0805", white="#d9a85c", mid="#5a4325")
    data = io.BytesIO()
    image.save(data, "JPEG", quality=80, optimize=True, progressive=True)
    encoded = base64.b64encode(data.getvalue()).decode()
    return f'<image href="data:image/jpeg;base64,{encoded}" width="{W}" height="{PICTURE_H}" preserveAspectRatio="xMidYMid slice"/>'


def mountains(seed: int) -> str:
    """Gold-lit mountain ranges under a starry sky, for projects without a screenshot."""
    rand = random.Random(seed)
    parts = [
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#0d0a08"/><stop offset=".6" stop-color="#2c1e11"/>'
        '<stop offset=".85" stop-color="#a8712f"/><stop offset="1" stop-color="#dca75f"/></linearGradient>',
        f'<rect width="{W}" height="{PICTURE_H}" fill="url(#sky)"/>',
    ]
    for _ in range(70):
        size = 0.6 + rand.random() ** 3 * 1.8
        parts.append(f'<circle cx="{rand.random() * W:.1f}" cy="{rand.random() * PICTURE_H * 0.6:.1f}" r="{size:.2f}" fill="#ffecd0" opacity="{0.3 + rand.random() * 0.7:.2f}"/>')
    mx, my, mr = W * 0.68, PICTURE_H * 0.3, 30
    parts.append(f'<circle cx="{mx:.0f}" cy="{my:.0f}" r="{mr}" fill="#0c0906"/>')
    # A thin lit edge on the moon's lower right, like the portfolio's screens.
    parts.append(f'<path d="M{mx + mr:.0f} {my:.0f}A{mr} {mr} 0 0 1 {mx:.0f} {my + mr:.0f}" fill="none" stroke="#ffd696" stroke-width="2"/>')
    for base, rough, color in ((0.62, 0.2, "#3a2a1a"), (0.74, 0.2, "#1d150e"), (0.88, 0.14, "#070504")):
        level = base
        points = [f"0,{PICTURE_H}"]
        for x in range(0, W + 40, 40):
            level = min(base + rough * 0.4, max(base - rough, level + (rand.random() - 0.5) * 0.11))
            points.append(f"{x},{PICTURE_H * level:.1f}")
        points.append(f"{W},{PICTURE_H}")
        parts.append(f'<polygon points="{" ".join(points)}" fill="{color}"/>')
    title = '<text x="420" y="168" text-anchor="middle" font-family="Display" font-size="54" letter-spacing="12" fill="#f4eee2">UP: VISIONS</text>'
    parts.append(title)
    return "".join(parts)


def tag_chips(tags: list[str]) -> tuple[str, str]:
    """Outlined labels along the bottom. Returns the SVG and the text used."""
    x = 36
    chips = []
    used = ""
    for tag in tags:
        label = tag.upper()
        used += label
        width = 22 + len(label) * 10.6
        chips.append(
            f'<rect x="{x}" y="470" width="{width:.0f}" height="30" fill="none" stroke="{LINE}"/>'
            f'<text x="{x + width / 2:.0f}" y="491" text-anchor="middle" font-family="Medium" font-size="16" letter-spacing="1.5" fill="{SOFT}">{escape(label)}</text>'
        )
        x += width + 10
    return "".join(chips), used


def card(spec: dict) -> str:
    title = spec["title"].upper()
    chips, chip_text = tag_chips(spec["tags"])
    art = picture(spec["picture"]) if spec["picture"] else mountains(4)
    display_text = title + spec["number"] + ("UP: VISIONS" if not spec["picture"] else "")
    styles = "".join(
        [
            font_face("Display", FONTS / "Rajdhani-SemiBold.woff2", display_text),
            font_face("Medium", FONTS / "Rajdhani-Medium.woff2", chip_text),
            font_face("Body", FONTS / "Barlow-Regular.woff2", spec["tagline"]),
        ]
    )
    bracket = 26
    # Cards take turns: a scan line crosses each picture in sequence, every few seconds.
    delay = (int(spec["number"]) - 1) * 1.6
    scan = (
        f'<rect x="-40" y="0" width="40" height="{PICTURE_H}" fill="url(#beam)">'
        f'<animate attributeName="x" dur="6.4s" begin="{delay}s" repeatCount="indefinite" keyTimes="0;.28;1" values="-40;{W};{W}"/></rect>'
    )
    pulse = '<animate attributeName="opacity" dur="3.2s" repeatCount="indefinite" values="1;.4;1"/>'
    nudge = '<animateTransform attributeName="transform" type="translate" dur="2.4s" repeatCount="indefinite" values="0 0;4 0;0 0"/>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(spec['title'])}: {escape(spec['tagline'])}">
<defs>
<style>{styles}</style>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
<stop offset=".45" stop-color="{INK}" stop-opacity="0"/><stop offset="1" stop-color="{INK}"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BRIGHT}" stop-opacity="0"/>
<stop offset=".85" stop-color="{BRIGHT}" stop-opacity=".22"/><stop offset="1" stop-color="{BRIGHT}" stop-opacity=".9"/></linearGradient>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="{INK}"/>
<g opacity=".88">{art}</g>
{scan}
<rect width="{W}" height="{PICTURE_H + 2}" fill="url(#fade)"/>
<text x="36" y="372" font-family="Display" font-size="22" letter-spacing="3" fill="{GOLD}">{spec['number']}</text>
<line x1="70" y1="365" x2="96" y2="365" stroke="{GOLD}" stroke-opacity=".6"/>
<text x="36" y="418" font-family="Display" font-size="40" letter-spacing="4" fill="{PALE}">{escape(title)}</text>
<text x="36" y="452" font-family="Body" font-size="21" letter-spacing=".4" fill="{SOFT}">{escape(spec['tagline'])}</text>
{chips}
<circle cx="786" cy="470" r="26" fill="{INK}" fill-opacity=".7" stroke="{GOLD}" stroke-opacity=".7"/>
<path d="M774 470h22m-8-8 8 8-8 8" fill="none" stroke="{GOLD}" stroke-width="2">{nudge}</path>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{LINE}"/>
<path d="M1 {bracket}V1h{bracket}M{W - 1} {H - bracket}V{H - 1}h-{bracket}" fill="none" stroke="{GOLD}" stroke-width="3">{pulse}</path>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in CARDS:
        svg = card(spec)
        path = OUT / f"{spec['file']}.svg"
        path.write_text(svg, encoding="utf8")
        print(f"{path.relative_to(ROOT)}  {len(svg.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
