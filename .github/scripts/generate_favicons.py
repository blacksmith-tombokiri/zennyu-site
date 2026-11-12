#!/usr/bin/env python3
"""Render the ぜんにゅー SVG mark into favicon images used by GitHub Pages."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SVG = ROOT / "favicon.svg"
SIZES = (16, 32, 48, 180, 192, 512)


def main() -> None:
    if not SVG.is_file():
        raise FileNotFoundError("favicon.svg must exist in the site root")
    png_bytes = cairosvg.svg2png(
        bytestring=SVG.read_bytes(), output_width=1024, output_height=1024
    )
    with Image.open(BytesIO(png_bytes)) as source:
        master = source.convert("RGBA").resize((512, 512), Image.Resampling.LANCZOS)
    if not master.getbbox():
        raise RuntimeError("Rendered favicon is empty")

    for size in SIZES:
        img = master if size == 512 else master.resize(
            (size, size), Image.Resampling.LANCZOS
        )
        img.save(ROOT / f"favicon-{size}x{size}.png", optimize=True)

    master.save(ROOT / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    for src_name, dest_name in (
        ("favicon-180x180.png", "apple-touch-icon.png"),
        ("favicon-192x192.png", "android-chrome-192x192.png"),
        ("favicon-512x512.png", "android-chrome-512x512.png"),
    ):
        (ROOT / dest_name).write_bytes((ROOT / src_name).read_bytes())

    with Image.open(ROOT / "favicon.ico") as icon:
        actual_sizes = icon.info.get("sizes", set())
    expected_sizes = {(16, 16), (32, 32), (48, 48)}
    if not expected_sizes.issubset(actual_sizes):
        raise RuntimeError(f"Missing ICO sizes: {expected_sizes - actual_sizes}")
    print("Generated transparent favicon images and multi-size ICO.")


if __name__ == "__main__":
    main()
