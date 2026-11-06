"""Builds the animated parts of the profile below the hero: intro, links, headings, stack, footer.

GitHub only allows images in a README, so each part is an SVG that animates itself with
SMIL, SVG's built-in animation. Links are separate images, each wrapped in its own link.

Run from the repo root:  python scripts/build_profile.py
"""

import math
from html import escape

from svgkit import BODY, BRIGHT, DISPLAY, GOLD, INK, LINE, MEDIUM, MUTED, PALE, ROOT, SOFT, font_face, frame, text_width

OUT = ROOT / "assets" / "profile"
W = 1200

NAME = "ADRIAN JOEL JASPA"
ROLES = ["DEVELOPER", "CREATIVE THINKER", "INTERACTIVE EXPERIENCES"]
INTRO = [
    "Developer from Iloilo, Philippines · Computer Science graduate, UP Visayas.",
    "I build interactive web experiences, from 3D portfolios to full-stack apps.",
]
LINKS = [
    ("portfolio", "PORTFOLIO", "adrian-js.vercel.app", "globe"),
    ("linkedin", "LINKEDIN", "in/adrianjaspa", "in"),
    ("x", "X", "@Aries_Leevi", "x"),
    ("resume", "RESUME", "One page, PDF", "page"),
]
STACK = ["TypeScript", "JavaScript", "React", "Next.js", "Three.js", "Tailwind CSS", "PostgreSQL", "Java", "C#", "PHP"]
SECTIONS = [("work", "02", "SELECTED WORK"), ("toolkit", "03", "TOOLKIT")]


def loop(attribute, seconds, times, values, extra=""):
    """An animation that repeats forever over `seconds`, from fractions and values."""
    return (
        f'<animate attributeName="{attribute}" dur="{seconds}s" repeatCount="indefinite" '
        f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" values="{";".join(str(v) for v in values)}"{extra}/>'
    )


def glow(cx, cy):
    return (
        f'<radialGradient id="glow" cx="{cx}" cy="{cy}" r="60%"><stop offset="0" stop-color="#2e1d0d"/>'
        f'<stop offset="1" stop-color="{INK}"/></radialGradient>'
    )


def ellipse_path(cx, cy, rx, ry):
    """An ellipse as a path, so dots can travel along it."""
    return f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 {-2 * rx} 0"


def intro():
    """The name types itself out, the roles take turns, and a small orbit turns beside it."""
    cycle = 12
    x, size, spacing = 56, 64, 8
    typing = 1.8
    widths, times = [0.0], [0.0]
    for i in range(1, len(NAME) + 1):
        widths.append(text_width(DISPLAY, NAME[:i], size, spacing))
        times.append(typing * i / len(NAME) / cycle)
    erase = 11.2 / cycle
    reveal = loop("width", cycle, times + [erase], [f"{w:.1f}" for w in widths] + [0], ' calcMode="discrete"')
    caret_x = loop("x", cycle, times + [erase], [f"{x + w + 6:.1f}" for w in widths] + [x], ' calcMode="discrete"')
    blink = '<animate attributeName="opacity" dur="1s" repeatCount="indefinite" values="1;0;1" keyTimes="0;.5;1" calcMode="discrete"/>'

    roles = []
    share = cycle / len(ROLES)
    for i, role in enumerate(ROLES):
        start, end = i * share / cycle, (i + 1) * share / cycle
        fade = 0.35 / cycle
        times_r = [0, max(start - fade, 0), start, end - fade, end, 1] if i else [0, end - fade, end, 1 - fade, 1]
        values_r = [0, 0, 1, 1, 0, 0] if i else [1, 1, 0, 0, 1]
        roles.append(
            f'<text x="{x + 26}" y="196" font-family="Display" font-size="22" letter-spacing="6" fill="{GOLD}" opacity="{values_r[0]}">{role}'
            f"{loop('opacity', cycle, times_r, values_r)}</text>"
        )

    cx, cy = 1000, 150
    rings = []
    for rx, ry, seconds, alpha, dot in ((86, 24, 7, 0.45, 3.2), (124, 36, 11, 0.32, 2.6), (160, 48, 16, 0.22, 2.2)):
        path = ellipse_path(cx, cy, rx, ry)
        rings.append(
            f'<path d="{path}" fill="none" stroke="{GOLD}" stroke-opacity="{alpha}" stroke-dasharray="2 9" stroke-width="1.4">'
            f'<animate attributeName="stroke-dashoffset" dur="{seconds / 3:.1f}s" repeatCount="indefinite" values="0;-22"/></path>'
            f'<circle r="{dot}" fill="{BRIGHT}"><animateMotion dur="{seconds}s" repeatCount="indefinite" path="{path}"/></circle>'
        )
    stars = "".join(
        f'<circle cx="{sx}" cy="{sy}" r="{r}" fill="#ffecd0" opacity="{o}">'
        f'<animate attributeName="opacity" dur="{d}s" repeatCount="indefinite" values="{o};.08;{o}"/></circle>'
        for sx, sy, r, o, d in ((870, 54, 1.2, .7, 3.1), (1132, 70, 1, .5, 4.3), (1150, 232, 1.4, .6, 2.7), (850, 240, 1, .4, 3.7), (1060, 40, 1.1, .5, 5.1), (930, 268, .9, .6, 4.6))
    )
    hole = (
        f'<circle cx="{cx}" cy="{cy}" r="34" fill="#000"/>'
        f'<circle cx="{cx}" cy="{cy}" r="35" fill="none" stroke="{BRIGHT}" stroke-width="2" stroke-opacity=".9"/>'
        f'<circle cx="{cx}" cy="{cy}" r="44" fill="none" stroke="{GOLD}" stroke-opacity=".18" stroke-width="10">'
        f'<animate attributeName="stroke-opacity" dur="4s" repeatCount="indefinite" values=".1;.28;.1"/></circle>'
    )
    # The front half of the rings passes in front of the hole.
    front = f'<clipPath id="front"><rect x="{cx - 200}" y="{cy}" width="400" height="80"/></clipPath>'

    intro_lines = "".join(
        f'<tspan x="{x}" y="{246 + i * 28}">{escape(line)}</tspan>' for i, line in enumerate(INTRO)
    )
    styles = (
        font_face("Display", DISPLAY, NAME + "".join(ROLES) + "//01IDENTITY")
        + font_face("Body", BODY, "".join(INTRO) + ">")
    )
    body = f"""<defs>{glow("80%", "50%")}<clipPath id="typed"><rect x="{x}" y="70" width="0" height="90">{reveal}</rect></clipPath>{front}</defs>
<rect width="{W}" height="300" fill="url(#glow)"/>
<text x="{x}" y="58" font-family="Display" font-size="15" letter-spacing="5" fill="{MUTED}">// 01  <tspan fill="{GOLD}">IDENTITY</tspan></text>
<g clip-path="url(#typed)"><text x="{x}" y="140" font-family="Display" font-size="{size}" letter-spacing="{spacing}" fill="{PALE}">{NAME}</text></g>
<rect x="{x}" y="92" width="4" height="54" fill="{GOLD}">{caret_x}{blink}</rect>
<text x="{x}" y="196" font-family="Body" font-size="20" fill="{MUTED}">&gt;</text>
{''.join(roles)}
<text font-family="Body" font-size="19" fill="{SOFT}">{intro_lines}</text>
{stars}{''.join(rings)}{hole}<g clip-path="url(#front)">{''.join(rings)}</g>"""
    return frame(W, 300, body, styles, f"{NAME.title()}: {', '.join(r.lower() for r in ROLES)}. {' '.join(INTRO)}")


def icon(kind, cx, cy):
    if kind == "globe":
        return (
            f'<circle cx="{cx}" cy="{cy}" r="11" fill="none" stroke="{GOLD}" stroke-width="2"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="5" ry="11" fill="none" stroke="{GOLD}" stroke-width="1.6"/>'
            f'<path d="M{cx - 11} {cy}h22" stroke="{GOLD}" stroke-width="1.6"/>'
        )
    if kind == "page":
        return (
            f'<path d="M{cx - 8} {cy - 12}h11l6 6v18h-17z" fill="none" stroke="{GOLD}" stroke-width="2" stroke-linejoin="round"/>'
            f'<path d="M{cx - 4} {cy - 1}h9M{cx - 4} {cy + 4}h9" stroke="{GOLD}" stroke-width="1.6"/>'
        )
    letter = "in" if kind == "in" else "X"
    return f'<text x="{cx}" y="{cy + 8}" text-anchor="middle" font-family="Display" font-size="23" fill="{GOLD}">{letter}</text>'


def link_button(index, label, sub, kind):
    """A gold button with a light that sweeps across it now and then."""
    w, h = 300, 84
    sweep = (
        f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BRIGHT}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{BRIGHT}" stop-opacity=".16"/><stop offset="1" stop-color="{BRIGHT}" stop-opacity="0"/></linearGradient>'
    )
    begin = f"{index * 0.9:.1f}s"
    styles = font_face("Display", DISPLAY, label + "inX") + font_face("Body", BODY, sub)
    body = f"""<defs>{sweep}</defs>
<rect width="{w}" height="{h}" fill="#120d08"/>
<circle cx="46" cy="42" r="24" fill="{INK}" stroke="{LINE}"/>
{icon(kind, 46, 42)}
<text x="84" y="40" font-family="Display" font-size="24" letter-spacing="4" fill="{PALE}">{label}</text>
<text x="84" y="62" font-family="Body" font-size="15" fill="{SOFT}">{escape(sub)}</text>
<path d="M266 46l10-10m-8 0h8v8" fill="none" stroke="{GOLD}" stroke-width="2">
<animateTransform attributeName="transform" type="translate" dur="2.4s" repeatCount="indefinite" values="0 0;2 -2;0 0"/></path>
<rect x="-160" y="0" width="140" height="{h}" fill="url(#shine)" transform="skewX(-20)">
<animate attributeName="x" dur="4.8s" begin="{begin}" repeatCount="indefinite" keyTimes="0;.3;1" values="-160;{w + 60};{w + 60}"/></rect>"""
    return frame(w, h, body, styles, f"{label.title()}: {sub}", corners=False)


def heading(number, title):
    """A section title with a gold line that draws itself, and a spark running along it."""
    h = 64
    title_x = 56 + text_width(DISPLAY, f"// {number}  ", 16, 5)
    line_start = title_x + text_width(DISPLAY, title, 22, 7) + 24
    length = W - 40 - line_start
    styles = font_face("Display", DISPLAY, f"// {number}  " + title)
    body = f"""<rect width="{W}" height="{h}" fill="#100b07"/>
<text x="56" y="39" font-family="Display" font-size="16" letter-spacing="5" fill="{MUTED}">// {number}</text>
<text x="{title_x:.0f}" y="40" font-family="Display" font-size="22" letter-spacing="7" fill="{PALE}">{title}</text>
<path d="M{line_start:.0f} 33h{length:.0f}" stroke="{LINE}" stroke-width="1"/>
<path d="M{line_start:.0f} 33h{length:.0f}" stroke="{GOLD}" stroke-width="1.5" stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}">
<animate attributeName="stroke-dashoffset" dur="6s" repeatCount="indefinite" keyTimes="0;.3;.8;1" values="{length:.0f};0;0;{-length:.0f}"/></path>
<circle cx="{line_start:.0f}" cy="33" r="3" fill="{BRIGHT}">
<animate attributeName="cx" dur="6s" repeatCount="indefinite" keyTimes="0;.3;1" values="{line_start:.0f};{line_start + length:.0f};{line_start + length:.0f}"/>
<animate attributeName="opacity" dur="6s" repeatCount="indefinite" keyTimes="0;.28;.34;1" values="1;1;0;0"/></circle>"""
    return frame(W, h, body, styles, f"Section {number}: {title.title()}", corners=False)


def stack():
    """The tools as chips. A glow passes from chip to chip, like a signal along a wire."""
    per_row, chip_w, chip_h, gap = 5, 206, 54, 16
    rows = -(-len(STACK) // per_row)
    h = 40 + rows * chip_h + (rows - 1) * gap + 40
    step = 0.55
    cycle = step * len(STACK) + 1.5
    chips = []
    for i, name in enumerate(STACK):
        col, row = i % per_row, i // per_row
        x = 56 + col * (chip_w + gap)
        y = 40 + row * (chip_h + gap)
        on = i * step / cycle
        peak = (i * step + 0.35) / cycle
        off = (i * step + 1.1) / cycle
        chips.append(
            f'<rect x="{x}" y="{y}" width="{chip_w}" height="{chip_h}" fill="{INK}" stroke="{LINE}">'
            f"{loop('stroke', cycle, [0, on, peak, off, 1], [LINE, LINE, GOLD, LINE, LINE])}</rect>"
            f'<rect x="{x}" y="{y}" width="3" height="{chip_h}" fill="{GOLD}" opacity=".35">'
            f"{loop('opacity', cycle, [0, on, peak, off, 1], ['.35', '.35', '1', '.35', '.35'])}</rect>"
            f'<text x="{x + 24}" y="{y + 35}" font-family="Medium" font-size="20" letter-spacing="3" fill="{SOFT}">{escape(name.upper())}'
            f"{loop('fill', cycle, [0, on, peak, off, 1], [SOFT, SOFT, BRIGHT, SOFT, SOFT])}</text>"
        )
    styles = font_face("Medium", MEDIUM, "".join(STACK).upper())
    body = f'<defs>{glow("50%", "50%")}</defs><rect width="{W}" height="{h}" fill="url(#glow)"/>{"".join(chips)}'
    return frame(W, h, body, styles, "Stack: " + ", ".join(STACK))


def footer():
    """A location signal that pings, beside a gold wave that keeps moving.

    The wave's soft ends come from a mask that stays still while the wave slides under it.
    """
    h = 110
    wave_w, period = 420, 60
    points = []
    for i in range(0, 2 * wave_w + 1, 4):
        y = 55 + 14 * math.sin(i / period * 2 * math.pi) * (0.6 + 0.4 * math.sin(i / (period * 3.5) * 2 * math.pi))
        points.append(f"{i},{y:.1f}")
    pings = "".join(
        f'<circle cx="70" cy="44" r="4" fill="none" stroke="{GOLD}" stroke-width="1.5">'
        f'<animate attributeName="r" dur="2.4s" begin="{d}s" repeatCount="indefinite" values="4;24"/>'
        f'<animate attributeName="opacity" dur="2.4s" begin="{d}s" repeatCount="indefinite" values=".9;0"/></circle>'
        for d in (0, 1.2)
    )
    top = "SIGNAL // ILOILO CITY, PHILIPPINES"
    bottom = "10.72° N · 122.56° E · Open to opportunities"
    credit = "Fonts: Rajdhani and Barlow, SIL Open Font License"
    styles = font_face("Display", DISPLAY, top) + font_face("Body", BODY, bottom + credit)
    body = f"""<defs>{glow("85%", "50%")}<clipPath id="wave"><rect x="700" y="0" width="{wave_w}" height="{h}"/></clipPath>
<linearGradient id="edges" x1="700" x2="{700 + wave_w}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset=".2" stop-color="#fff"/><stop offset=".8" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="soft"><rect x="700" y="0" width="{wave_w}" height="{h}" fill="url(#edges)"/></mask></defs>
<rect width="{W}" height="{h}" fill="url(#glow)"/>
{pings}<circle cx="70" cy="44" r="5" fill="{BRIGHT}"/>
<text x="104" y="50" font-family="Display" font-size="17" letter-spacing="5" fill="{GOLD}">{top}</text>
<text x="104" y="76" font-family="Body" font-size="16" fill="{SOFT}">{bottom}</text>
<g clip-path="url(#wave)" mask="url(#soft)"><polyline points="{" ".join(points)}" fill="none" stroke="{GOLD}" stroke-width="1.8" transform="translate(700 0)">
<animateTransform attributeName="transform" type="translate" dur="6s" repeatCount="indefinite" values="700 0;{700 - wave_w} 0"/></polyline></g>
<text x="{W - 40}" y="{h - 14}" text-anchor="end" font-family="Body" font-size="12" fill="{MUTED}">{credit}</text>"""
    return frame(W, h, body, styles, f"{top.title()}. {bottom}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {"intro.svg": intro(), "stack.svg": stack(), "footer.svg": footer()}
    for index, (name, label, sub, kind) in enumerate(LINKS):
        files[f"link-{name}.svg"] = link_button(index, label, sub, kind)
    for name, number, title in SECTIONS:
        files[f"heading-{name}.svg"] = heading(number, title)
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf8")
        print(f"assets/profile/{name}  {len(svg.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
