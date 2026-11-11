#!/usr/bin/env python3
"""Render public-category OGP thumbnails in the same visual language as the site."""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
WIDTH, HEIGHT = 1200, 630
# Same two endpoints as zennyu/image-fixes.css and zennyu/index.html.
CATEGORIES = {
    "good": ("善", "#f2c5bf", "#cc7c72"),
    "forward": ("前", "#b9cbe5", "#6f8fc0"),
    "nature": ("然", "#b9d8ba", "#6a9a70"),
    "repair": ("繕", "#e2c4a7", "#aa7548"),
    "mind": ("禅", "#d0c7e2", "#8775ad"),
    "food": ("膳", "#eddcae", "#c49b42"),
}
FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
)


def hex_rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(bytes.fromhex(hex_color.lstrip("#")))


def render(name: str, character: str, first: str, last: str, font_path: Path) -> None:
    # Approximate CSS linear-gradient(145deg, first, last), over the 1200x630 image.
    a, b = hex_rgb(first), hex_rgb(last)
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()
    angle = math.radians(145 - 90)
    dx, dy = math.cos(angle), math.sin(angle)
    corners = [x * dx + y * dy for x in (0, WIDTH) for y in (0, HEIGHT)]
    low, high = min(corners), max(corners)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            t = max(0.0, min(1.0, (x * dx + y * dy - low) / (high - low)))
            pixels[x, y] = tuple(round((1 - t) * left + t * right) for left, right in zip(a, b))
    # Same central translucent kanji used by the article's CSS fallback image.
    text_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    drawer = ImageDraw.Draw(text_layer)
    font = ImageFont.truetype(str(font_path), 370)
    bounds = drawer.textbbox((0, 0), character, font=font, stroke_width=0)
    text_width, text_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    x = (WIDTH - text_width) / 2 - bounds[0]
    y = (HEIGHT - text_height) / 2 - bounds[1]
    drawer.text((round(x), round(y)), character, font=font, fill=(255, 255, 255, 85))
    image = Image.alpha_composite(image.convert("RGBA"), text_layer).convert("RGB")
    path = ROOT / f"og-category-{name}.png"
    image.save(path, format="PNG", optimize=True)
    print(f"Rendered {path.name} ({path.stat().st_size} bytes)")


def main() -> None:
    font = next((Path(path) for path in FONT_CANDIDATES if Path(path).is_file()), None)
    if font is None:
        raise RuntimeError("Japanese Noto Sans CJK font is missing. Install fonts-noto-cjk.")
    for name, (kanji, first, last) in CATEGORIES.items():
        render(name, kanji, first, last, font)


if __name__ == "__main__":
    main()
