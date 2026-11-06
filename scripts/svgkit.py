"""Shared pieces for the profile's SVGs: colours, fonts and text measuring."""

import base64
import io
from functools import lru_cache
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

GOLD = "#f0bb66"
BRIGHT = "#ffe1a8"
PALE = "#f4eee2"
SOFT = "#b9ad9a"
MUTED = "#7d705d"
INK = "#0b0805"
LINE = "#5a4325"

DISPLAY = FONTS / "Rajdhani-SemiBold.woff2"
MEDIUM = FONTS / "Rajdhani-Medium.woff2"
BODY = FONTS / "Barlow-Regular.woff2"


def font_face(family: str, path: Path, text: str) -> str:
    """A @font-face rule holding only the letters in `text`, so each SVG stays small.

    GitHub shows README images through a proxy that blocks outside files,
    so fonts have to live inside the SVG itself.
    """
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


@lru_cache
def _metrics(path: Path):
    font = TTFont(path)
    return font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm


def text_width(path: Path, text: str, size: float, spacing: float = 0) -> float:
    """How wide a line of text renders, so animations can be fitted to it exactly."""
    cmap, metrics, units = _metrics(path)
    width = sum(metrics[cmap[ord(char)]][0] for char in text if ord(char) in cmap) * size / units
    return width + spacing * len(text)


def frame(width: int, height: int, body: str, styles: str, label: str, corners: bool = True) -> str:
    """A dark rounded panel with the portfolio's gold corner brackets."""
    brackets = (
        f'<path d="M1 26V1h25M{width - 1} {height - 26}V{height - 1}h-25" fill="none" stroke="{GOLD}" stroke-width="3"/>'
        if corners
        else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{label}">
<defs><style>{styles}text{{font-variant-ligatures:none}}</style>
<clipPath id="panel"><rect width="{width}" height="{height}" rx="10"/></clipPath></defs>
<g clip-path="url(#panel)">{body}</g>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="none" stroke="{LINE}"/>
{brackets}
</svg>
"""
