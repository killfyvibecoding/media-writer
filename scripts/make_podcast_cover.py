#!/usr/bin/env python3
"""Create a horizontal text-led cover image for NotebookLM podcast outputs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install it with: python -m pip install Pillow"
    ) from exc


THEMES = {
    "editorial": {
        "bg": (18, 24, 31),
        "panel": (244, 239, 225),
        "accent": (239, 83, 80),
        "accent2": (24, 126, 115),
        "text": (248, 248, 244),
        "muted": (204, 210, 214),
        "dark_text": (21, 26, 32),
        "chip": (38, 48, 58),
    },
    "ai-infra": {
        "bg": (13, 18, 24),
        "panel": (236, 231, 216),
        "accent": (245, 174, 52),
        "accent2": (74, 164, 145),
        "text": (247, 247, 242),
        "muted": (193, 201, 207),
        "dark_text": (18, 23, 29),
        "chip": (39, 47, 55),
    },
    "business-story": {
        "bg": (24, 23, 21),
        "panel": (239, 232, 218),
        "accent": (181, 104, 65),
        "accent2": (92, 132, 140),
        "text": (247, 242, 232),
        "muted": (209, 201, 189),
        "dark_text": (29, 27, 24),
        "chip": (49, 43, 37),
    },
    "knowledge-card": {
        "bg": (245, 240, 232),
        "panel": (22, 30, 38),
        "accent": (232, 101, 90),
        "accent2": (79, 143, 129),
        "text": (28, 32, 36),
        "muted": (79, 90, 98),
        "dark_text": (244, 240, 232),
        "chip": (227, 220, 207),
    },
    "tech-blueprint": {
        "bg": (9, 25, 42),
        "panel": (226, 236, 239),
        "accent": (65, 164, 203),
        "accent2": (137, 203, 190),
        "text": (238, 246, 248),
        "muted": (180, 207, 217),
        "dark_text": (13, 34, 50),
        "chip": (26, 55, 78),
    },
    "warm-human": {
        "bg": (48, 36, 31),
        "panel": (248, 236, 213),
        "accent": (218, 138, 85),
        "accent2": (190, 95, 82),
        "text": (250, 242, 228),
        "muted": (226, 207, 187),
        "dark_text": (54, 38, 31),
        "chip": (74, 53, 45),
    },
    "dark-cinematic": {
        "bg": (10, 12, 16),
        "panel": (232, 226, 211),
        "accent": (208, 46, 60),
        "accent2": (218, 171, 82),
        "text": (245, 245, 238),
        "muted": (186, 190, 194),
        "dark_text": (17, 18, 22),
        "chip": (31, 35, 43),
    },
    "minimal-mono": {
        "bg": (238, 238, 234),
        "panel": (22, 22, 21),
        "accent": (38, 38, 36),
        "accent2": (113, 113, 107),
        "text": (24, 24, 23),
        "muted": (78, 78, 73),
        "dark_text": (246, 246, 242),
        "chip": (222, 222, 216),
    },
}


FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_CANDIDATES if bold else FONT_CANDIDATES[1:] + FONT_CANDIDATES[:1]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def visual_len(text: str) -> float:
    return sum(1.8 if ord(ch) > 127 else 1.0 for ch in text)


def wrap_text(text: str, max_units: float) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []

    lines: list[str] = []
    current = ""
    for token in re.findall(r"[\u4e00-\u9fff]|[^\u4e00-\u9fff\s]+|\s+", text):
        if token.isspace():
            candidate = current + " "
        else:
            candidate = current + token
        if current and visual_len(candidate) > max_units:
            lines.append(current.strip())
            current = token.strip()
        else:
            current = candidate
    if current.strip():
        lines.append(current.strip())
    return lines


def fit_title(title: str, width: int) -> tuple[ImageFont.ImageFont, list[str]]:
    for size in range(116, 62, -4):
        title_font = font(size, bold=True)
        approx_units = max(9, width / (size * 0.56))
        lines = wrap_text(title, approx_units)
        if len(lines) <= 3:
            return title_font, lines[:3]
    return font(64, bold=True), wrap_text(title, 17)[:3]


def draw_round_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    radius: int = 22,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def draw_cover(args: argparse.Namespace) -> None:
    width, height = args.width, args.height
    theme = THEMES[args.theme]

    img = Image.new("RGB", (width, height), theme["bg"])
    draw = ImageDraw.Draw(img)

    # Subtle editorial structure without depending on external assets.
    draw.rectangle((0, 0, width, height), fill=theme["bg"])
    draw.rectangle((0, 0, 48, height), fill=theme["accent"])
    draw.rectangle((48, height - 88, width, height), fill=theme["panel"])
    draw.polygon(
        [(width - 620, 0), (width, 0), (width, height), (width - 220, height)],
        fill=(23, 31, 39),
    )
    draw.line((116, 128, width - 150, 128), fill=theme["accent2"], width=6)

    badge_font = font(34, bold=True)
    badge = args.badge.strip()
    if badge:
        badge_w = int(draw.textlength(badge, font=badge_font)) + 52
        draw_round_rect(draw, (116, 178, 116 + badge_w, 246), theme["chip"], radius=18)
        draw.text((142, 192), badge, font=badge_font, fill=theme["muted"])

    title_font, title_lines = fit_title(args.title, width - 360)
    y = 340
    for line in title_lines:
        draw.text((116, y), line, font=title_font, fill=theme["text"])
        y += int(title_font.size * 1.18)

    subtitle_lines = wrap_text(args.subtitle, 28)[:2]
    subtitle_font = font(48, bold=False)
    y += 38
    for line in subtitle_lines:
        draw.text((120, y), line, font=subtitle_font, fill=theme["muted"])
        y += 64

    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    tag_font = font(32, bold=True)
    tag_x, tag_y = 120, height - 210
    for tag in tags[:4]:
        text_w = int(draw.textlength(tag, font=tag_font))
        draw_round_rect(draw, (tag_x, tag_y, tag_x + text_w + 44, tag_y + 56), theme["chip"], radius=16)
        draw.text((tag_x + 22, tag_y + 12), tag, font=tag_font, fill=theme["muted"])
        tag_x += text_w + 66

    footer_font = font(34, bold=True)
    footer = args.footer.strip()
    if footer:
        draw.text((120, height - 64), footer, font=footer_font, fill=theme["dark_text"])

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, quality=94, optimize=True)
    print(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a 16:9 podcast cover image.")
    parser.add_argument("--title", required=True, help="Main cover title.")
    parser.add_argument("--subtitle", default="", help="One-sentence hook.")
    parser.add_argument("--badge", default="NotebookLM Podcast", help="Small top badge.")
    parser.add_argument("--footer", default="Generated from source notes", help="Footer label.")
    parser.add_argument("--tags", default="播客,AI 摘要,深度复盘", help="Comma-separated chips.")
    parser.add_argument("--output", required=True, help="Output JPG path.")
    parser.add_argument("--width", type=int, default=2560)
    parser.add_argument("--height", type=int, default=1440)
    parser.add_argument("--theme", choices=sorted(THEMES), default="ai-infra")
    return parser.parse_args()


if __name__ == "__main__":
    draw_cover(parse_args())
