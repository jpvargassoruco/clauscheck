#!/usr/bin/env python3
"""Genera los iconos PWA de ClausCheck (monograma "CC" azul/dorado).

Uso: python3 scripts/gen_icons.py
Requiere Pillow (pip install pillow). Escribe en web/public/icons/.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AZUL = (30, 58, 138, 255)  # #1E3A8A
DORADO = (201, 162, 39, 255)  # #C9A227
BLANCO = (255, 255, 255, 255)

OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "icons"


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_icon(size: int, maskable: bool) -> Image.Image:
    img = Image.new("RGBA", (size, size), AZUL)
    draw = ImageDraw.Draw(img)

    # Safe-zone padding for maskable icons (≈10% margin per spec).
    pad = int(size * 0.16) if maskable else 0

    # Dorado accent bar behind the monogram.
    bar_h = int(size * 0.14)
    draw.rectangle(
        [0, size - bar_h - pad, size, size - pad], fill=DORADO
    )

    text = "CC"
    font_size = int(size * (0.46 if maskable else 0.52))
    font = _font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) / 2 - bbox[0]
    y = (size - h) / 2 - bbox[1] - bar_h / 2
    draw.text((x, y), text, font=font, fill=BLANCO)

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-192.png", 192, True),
        ("icon-maskable-512.png", 512, True),
    ]
    for name, size, maskable in specs:
        icon = make_icon(size, maskable)
        icon.save(OUT_DIR / name)
        print(f"escrito {OUT_DIR / name}")


if __name__ == "__main__":
    main()
