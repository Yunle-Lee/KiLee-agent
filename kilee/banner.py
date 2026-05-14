"""ASCII banner generator — convert images to terminal startup banners.

Inspired by the Custom TUI Generator at kilee.cn.
Supports multiple character sets and color themes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from kilee import config, theme

console = Console(highlight=False)

AC = theme.C["accent"]
AC2 = theme.C["accent2"]
DM = theme.C["dim"]
OK = theme.C["ok"]
ERR = theme.C["error"]
BDR = theme.C["border"]

CHAR_SETS = {
    "detailed": ["█", "▓", "▒", "░", "◆", "◈", "◇", "○", "●", "◎", "◐", "◑", " "],
    "blocks":   ["█", "▓", "▒", "░", " "],
    "classic":  ["@", "#", "S", "%", "?", "*", "+", ";", ":", " "],
    "minimal":  ["●", "◆", "◈", "◇", "○", " "],
}

BANNER_CONFIG_PATH = os.path.expanduser("~/.kilee/banner.json")

DEFAULT_BANNER = {
    "logo": "blocks",
    "name": "KiLee",
    "tagline": "Agent v0.3",
    "color": "#00CFCF",
}


def image_to_ascii(
    image_path: str,
    width: int = 60,
    char_set: str = "blocks",
) -> str:
    """Convert an image file to ASCII art string."""
    try:
        from PIL import Image
    except ImportError:
        return None

    chars = CHAR_SETS.get(char_set, CHAR_SETS["blocks"])
    img = Image.open(image_path)
    aspect = 0.55
    height = round((img.height / img.width) * width * aspect)
    img = img.resize((width, height))
    img = img.convert("L")

    pixels = list(img.getdata())
    ascii_lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            brightness = pixels[y * width + x] / 255
            idx = min(int(brightness * (len(chars) - 1)), len(chars) - 1)
            line += chars[len(chars) - 1 - idx]
        ascii_lines.append(line)

    return "\n".join(ascii_lines)


def build_banner(
    ascii_art: str = None,
    name: str = "KiLee",
    tagline: str = "Agent v0.3",
    width: int = 60,
) -> str:
    sep = "─" * min(width, 60)

    def pad(s: str, w: int) -> str:
        p = max(0, (w - len(s)) // 2)
        return " " * p + s

    lines = [sep]
    if ascii_art:
        lines.append(ascii_art.rstrip("\n"))
    lines += [
        sep,
        pad(f"◈ {name} ◈", min(width, 60)),
        pad(tagline, min(width, 60)),
        sep,
    ]
    return "\n".join(lines)


def save_banner_config(cfg: dict):
    os.makedirs(os.path.dirname(BANNER_CONFIG_PATH), exist_ok=True)
    with open(BANNER_CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def load_banner_config() -> dict:
    if os.path.exists(BANNER_CONFIG_PATH):
        try:
            with open(BANNER_CONFIG_PATH) as f:
                return {**DEFAULT_BANNER, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_BANNER.copy()


def get_custom_banner() -> Optional[str]:
    cfg = load_banner_config()
    logo_path = cfg.get("logo", "")
    if logo_path and Path(logo_path).expanduser().exists():
        ascii_art = image_to_ascii(
            str(Path(logo_path).expanduser()),
            width=60,
            char_set="blocks",
        )
        if ascii_art:
            return build_banner(
                ascii_art=ascii_art,
                name=cfg.get("name", "KiLee"),
                tagline=cfg.get("tagline", ""),
                width=60,
            )
    return None
