"""
assets.py - Font Manager với hỗ trợ tiếng Việt đầy đủ
"""

import pygame
import os
import sys

from src.constants import (
    FONTS_DIR, FONT_XL, FONT_LG, FONT_MD, FONT_SM, FONT_XS,
)


def _find_unicode_font_path() -> str | None:
    """Tìm file .ttf hỗ trợ Unicode trên hệ thống."""
    candidates = []

    if sys.platform.startswith("win"):
        windir = os.environ.get("WINDIR", "C:\\Windows")
        wf = os.path.join(windir, "Fonts")
        candidates = [
            os.path.join(wf, "segoeui.ttf"),
            os.path.join(wf, "arial.ttf"),
            os.path.join(wf, "tahoma.ttf"),
            os.path.join(wf, "calibri.ttf"),
            os.path.join(wf, "verdana.ttf"),
        ]
    elif sys.platform.startswith("darwin"):
        candidates = [
            "/Library/Fonts/Arial Unicode MS.ttf",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:
        # Linux
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]

    for p in candidates:
        if os.path.isfile(p):
            return p

    # Fallback: pygame.font.match_font
    for name in ["dejavusans", "notosans", "freesans", "liberationsans",
                 "arial", "segoeui", "ubuntu", "tahoma", "sans"]:
        p = pygame.font.match_font(name)
        if p and os.path.isfile(p):
            return p

    return None


def _find_bold_path(regular_path: str | None) -> str | None:
    """Tìm bold variant của font regular."""
    if not regular_path:
        return None
    for suffix in [("Regular", "Bold"), ("regular", "bold"), (".ttf", "Bold.ttf")]:
        if suffix[0] in regular_path:
            bold_p = regular_path.replace(suffix[0], suffix[1])
            if os.path.isfile(bold_p):
                return bold_p
    return regular_path  # dùng chính nó, pygame sẽ giả lập bold


def _make_font(path: str | None, size: int, bold: bool = False) -> pygame.font.Font:
    """Load font an toàn với nhiều fallback."""
    target = path
    if bold:
        bp = _find_bold_path(path)
        if bp:
            target = bp

    if target:
        try:
            f = pygame.font.Font(target, size)
            if bold and target == path:
                f.set_bold(True)  # giả lập bold nếu không có file bold riêng
            return f
        except Exception:
            pass

    # SysFont fallback
    for name in ["dejavusans", "freesans", "arial", "sans"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass

    return pygame.font.Font(None, size + 6)


class AssetManager:
    """Singleton quản lý font toàn game với Unicode / tiếng Việt."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._fonts = {}
        self._path = None
        self._load()

    def _load(self):
        self._path = _find_unicode_font_path()
        if self._path:
            print(f"[Font] OK: {os.path.basename(self._path)}")
        else:
            print("[Font] WARNING: No unicode TTF found — Vietnamese may not display")

        sizes = {"xl": FONT_XL, "lg": FONT_LG, "md": FONT_MD, "sm": FONT_SM, "xs": FONT_XS}
        for key, sz in sizes.items():
            self._fonts[key]            = _make_font(self._path, sz, bold=False)
            self._fonts[f"{key}_bold"]  = _make_font(self._path, sz, bold=True)

    def font(self, size: str = "md", bold: bool = False) -> pygame.font.Font:
        key = f"{size}_bold" if bold else size
        return self._fonts.get(key) or self._fonts["md"]

    def render_text(
        self,
        text: str,
        size: str = "md",
        color=(255, 255, 255),
        bold: bool = False,
        antialias: bool = True,
        shadow: bool = False,
        shadow_color=(0, 0, 0),
        shadow_offset: int = 2,
    ) -> pygame.Surface:
        f = self.font(size, bold)
        try:
            surf = f.render(text, antialias, color)
        except Exception:
            safe = text.encode("ascii", errors="replace").decode("ascii")
            surf = f.render(safe, antialias, color)

        if shadow:
            try:
                sh = f.render(text, antialias, shadow_color)
            except Exception:
                safe = text.encode("ascii", errors="replace").decode("ascii")
                sh = f.render(safe, antialias, shadow_color)
            combined = pygame.Surface(
                (surf.get_width() + shadow_offset, surf.get_height() + shadow_offset),
                pygame.SRCALPHA
            )
            combined.blit(sh, (shadow_offset, shadow_offset))
            combined.blit(surf, (0, 0))
            return combined

        return surf

    def render_text_wrapped(
        self,
        text: str,
        max_width: int,
        size: str = "sm",
        color=(255, 255, 255),
        bold: bool = False,
        line_spacing: int = 8,
    ) -> pygame.Surface:
        f = self.font(size, bold)
        lines = []

        for para in text.split("\n"):
            words = para.split()
            if not words:
                lines.append("")
                continue
            cur = []
            for word in words:
                test = " ".join(cur + [word])
                try:
                    w = f.size(test)[0]
                except Exception:
                    w = len(test) * 10
                if w <= max_width:
                    cur.append(word)
                else:
                    if cur:
                        lines.append(" ".join(cur))
                    cur = [word]
            if cur:
                lines.append(" ".join(cur))

        if not lines:
            lines = [""]

        lh = f.get_linesize() + line_spacing
        surf = pygame.Surface((max(1, max_width), max(1, lh * len(lines))), pygame.SRCALPHA)
        for i, line in enumerate(lines):
            if not line:
                continue
            try:
                rs = f.render(line, True, color)
            except Exception:
                safe = line.encode("ascii", errors="replace").decode("ascii")
                rs = f.render(safe, True, color)
            surf.blit(rs, (0, i * lh))
        return surf


assets = AssetManager()