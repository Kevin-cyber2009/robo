"""
ui_components.py - Thư viện UI Components
"""

import pygame
import math
from src.constants import *
from src.assets import assets


class Button:

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        text: str,
        color_normal=CYAN,
        color_hover=WHITE,
        bg_normal=PANEL_BG,
        bg_hover=CYAN,
        font_size: str = "md",
        icon: str = "",
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.icon = icon
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.bg_normal = bg_normal
        self.bg_hover = bg_hover
        self.font_size = font_size

        # Trạng thái animation
        self._hover_t = 0.0     # 0.0 → 1.0 (lerp animation)
        self._click_t = 0.0     # Flash khi click
        self.hovered = False
        self.clicked = False    # True trong 1 frame khi được click

        # Để detect click (chỉ fire 1 lần per press)
        self._was_pressed = False

    def update(self, events: list, dt: float) -> bool:
        """
        Cập nhật trạng thái nút.
        """
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.clicked = False

        # Smooth hover animation
        target = 1.0 if self.hovered else 0.0
        self._hover_t += (target - self._hover_t) * min(ANIM_SPEED * dt * 8, 1.0)

        # Click detection
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered:
                    self._click_t = 1.0
                    self.clicked = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._was_pressed = False

        # Click flash fade
        self._click_t = max(0.0, self._click_t - dt * 6)

        return self.clicked

    def draw(self, surface: pygame.Surface):
        """Vẽ nút với hiệu ứng hover và click."""
        t = self._hover_t

        # Màu nền (lerp)
        bg = _lerp_color(self.bg_normal, self.bg_hover, t)
        text_color = _lerp_color(self.color_normal, self.color_hover, t)

        # Scale khi click
        scale = 1.0 - self._click_t * 0.04
        draw_rect = _scale_rect(self.rect, scale)

        # Vẽ glow khi hover
        if t > 0.05:
            glow_surf = pygame.Surface(
                (draw_rect.width + 20, draw_rect.height + 20), pygame.SRCALPHA
            )
            glow_color = (*self.bg_hover, int(60 * t))
            pygame.draw.rect(
                glow_surf, glow_color,
                glow_surf.get_rect(), border_radius=BUTTON_RADIUS + 4
            )
            surface.blit(glow_surf, (draw_rect.x - 10, draw_rect.y - 10))

        # Nền nút
        pygame.draw.rect(surface, bg, draw_rect, border_radius=BUTTON_RADIUS)

        # Viền nút
        border_color = _lerp_color(CYAN_DIM, self.bg_hover, t)
        pygame.draw.rect(
            surface, border_color, draw_rect,
            width=2, border_radius=BUTTON_RADIUS
        )

        # Hiển thị text
        label = f"{self.icon} {self.text}" if self.icon else self.text
        text_surf = assets.render_text(label, self.font_size, text_color, bold=True)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)


class Panel:
    """Khung nền mờ với viền trang trí."""

    def __init__(
        self, x: int, y: int, width: int, height: int,
        color=PANEL_BG, border_color=CYAN_DIM,
        alpha: int = 220, radius: int = 12
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.border_color = border_color
        self.alpha = alpha
        self.radius = radius

    def draw(self, surface: pygame.Surface):
        surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_color = (*self.color, self.alpha)
        pygame.draw.rect(surf, bg_color, surf.get_rect(), border_radius=self.radius)
        pygame.draw.rect(
            surf, (*self.border_color, 200),
            surf.get_rect(), width=2, border_radius=self.radius
        )
        surface.blit(surf, self.rect.topleft)


class HealthBar:
    """Thanh máu robot với animation mượt và đổi màu theo %."""

    def __init__(self, x: int, y: int, width: int, height: int = 20):
        self.rect = pygame.Rect(x, y, width, height)
        self._display_ratio = 1.0   # Giá trị hiển thị (animate)
        self.target_ratio = 1.0     # Giá trị thực

    def set_ratio(self, current: float, maximum: float):
        self.target_ratio = max(0.0, min(1.0, current / maximum))

    def update(self, dt: float):
        # Animate thanh máu giảm dần
        self._display_ratio += (
            (self.target_ratio - self._display_ratio) * min(dt * 8, 1.0)
        )

    def draw(self, surface: pygame.Surface):
        # Nền thanh máu
        pygame.draw.rect(surface, GRAY_DARK, self.rect, border_radius=6)

        # Màu theo % máu
        r = self._display_ratio
        if r > 0.6:
            color = HP_HIGH
        elif r > 0.3:
            color = HP_MED
        else:
            color = HP_LOW

        # Phần máu còn lại
        fill_w = int(self.rect.width * r)
        if fill_w > 4:
            fill_rect = pygame.Rect(
                self.rect.x, self.rect.y, fill_w, self.rect.height
            )
            pygame.draw.rect(surface, color, fill_rect, border_radius=6)

        # Glow ở đầu thanh máu
        if fill_w > 10:
            glow_x = self.rect.x + fill_w - 6
            glow_surf = pygame.Surface((12, self.rect.height), pygame.SRCALPHA)
            glow_color = (*color, 180)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect())
            surface.blit(glow_surf, (glow_x, self.rect.y))

        # Viền
        pygame.draw.rect(surface, CYAN_DIM, self.rect, width=2, border_radius=6)

        # Text % máu
        pct = int(r * 100)
        txt = assets.render_text(f"HP: {pct}%", "xs", WHITE)
        surface.blit(txt, (self.rect.x + 6, self.rect.y + 2))


class TextInput:
    """
    Ô nhập liệu văn bản với cursor nhấp nháy.
    """

    def __init__(
        self, x: int, y: int, width: int, height: int = 48,
        placeholder: str = "Nhập câu trả lời...",
        max_length: int = 200,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.max_length = max_length
        self.text = ""
        self.active = False
        self._cursor_timer = 0.0
        self._cursor_visible = True

    def update(self, events: list, dt: float):
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)

            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key not in (
                    pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE
                ):
                    if len(self.text) < self.max_length:
                        # pygame.KEYDOWN unicode hỗ trợ tiếng Việt
                        if event.unicode and event.unicode.isprintable():
                            self.text += event.unicode

    def draw(self, surface: pygame.Surface):
        # Nền
        bg_color = PANEL_BG if not self.active else (30, 40, 65)
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)

        # Viền
        border = CYAN if self.active else GRAY_DARK
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=8)

        # Text hoặc placeholder
        if self.text:
            display = self.text
            color = WHITE
        else:
            display = self.placeholder
            color = GRAY

        # Cắt text nếu quá dài
        font = assets.font("sm")
        max_w = self.rect.width - 20
        while font.size(display)[0] > max_w and len(display) > 1:
            display = display[1:]

        txt_surf = assets.render_text(display, "sm", color)
        txt_y = self.rect.y + (self.rect.height - txt_surf.get_height()) // 2
        surface.blit(txt_surf, (self.rect.x + 10, txt_y))

        # Cursor nhấp nháy
        if self.active and self._cursor_visible:
            cursor_x = self.rect.x + 10 + font.size(display)[0] + 2
            cursor_top = txt_y + 2
            cursor_bot = txt_y + txt_surf.get_height() - 2
            pygame.draw.line(surface, CYAN, (cursor_x, cursor_top), (cursor_x, cursor_bot), 2)

    @property
    def value(self) -> str:
        return self.text.strip()

    def clear(self):
        self.text = ""


class Checkbox:
    """Hộp chọn có thể toggle True/False."""

    def __init__(self, x: int, y: int, size: int = 28, label: str = ""):
        self.rect = pygame.Rect(x, y, size, size)
        self.label = label
        self.checked = False
        self._hover = False

    def update(self, events: list):
        mouse_pos = pygame.mouse.get_pos()
        self._hover = self.rect.collidepoint(mouse_pos)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._hover:
                    self.checked = not self.checked

    def draw(self, surface: pygame.Surface):
        bg = PANEL_BG
        border = CYAN if self._hover else GRAY_DARK
        pygame.draw.rect(surface, bg, self.rect, border_radius=5)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=5)

        if self.checked:
            # Dấu tick ✓
            margin = 5
            p1 = (self.rect.x + margin, self.rect.centery)
            p2 = (self.rect.centerx - 2, self.rect.bottom - margin)
            p3 = (self.rect.right - margin, self.rect.top + margin)
            pygame.draw.lines(surface, GREEN, False, [p1, p2, p3], 3)

        if self.label:
            lbl = assets.render_text(self.label, "sm", WHITE)
            surface.blit(lbl, (self.rect.right + 10, self.rect.centery - lbl.get_height() // 2))


class ScrollList:
    """
    Danh sách item có thể cuộn bằng chuột.
    """

    def __init__(
        self, x: int, y: int, width: int, height: int,
        item_h: int = 44, multi_select: bool = False
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.item_h = item_h
        self.multi_select = multi_select
        self.items = []         # List of dict
        self.scroll_y = 0
        self._max_scroll = 0
        self.selected_ids = set()

    def set_items(self, items: list):
        self.items = items
        total_h = len(items) * self.item_h
        self._max_scroll = max(0, total_h - self.rect.height)
        self.scroll_y = 0
        self.selected_ids = set()

    def update(self, events: list):
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                if self.rect.collidepoint(pygame.mouse.get_pos()):
                    self.scroll_y -= event.y * self.item_h
                    self.scroll_y = max(0, min(self._max_scroll, self.scroll_y))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self.rect.collidepoint(mx, my):
                    # Tính item được click
                    rel_y = my - self.rect.y + self.scroll_y
                    idx = int(rel_y // self.item_h)
                    if 0 <= idx < len(self.items):
                        item_id = self.items[idx]["id"]
                        if self.multi_select:
                            if item_id in self.selected_ids:
                                self.selected_ids.discard(item_id)
                            else:
                                self.selected_ids.add(item_id)
                        else:
                            self.selected_ids = {item_id}

    def draw(self, surface: pygame.Surface):
        # Clip vùng danh sách
        clip_surf = pygame.Surface(
            (self.rect.width, self.rect.height), pygame.SRCALPHA
        )

        for i, item in enumerate(self.items):
            item_y = i * self.item_h - self.scroll_y
            if item_y + self.item_h < 0 or item_y > self.rect.height:
                continue

            item_rect = pygame.Rect(0, item_y, self.rect.width, self.item_h - 2)
            selected = item["id"] in self.selected_ids

            bg = (40, 60, 90) if selected else PANEL_BG
            pygame.draw.rect(clip_surf, bg, item_rect, border_radius=6)

            border_c = CYAN if selected else GRAY_DARK
            pygame.draw.rect(clip_surf, border_c, item_rect, width=1, border_radius=6)

            txt_color = CYAN if selected else GRAY_LIGHT
            txt_surf = assets.render_text(item.get("text", ""), "sm", txt_color)
            clip_surf.blit(txt_surf, (12, item_y + (self.item_h - txt_surf.get_height()) // 2))

            # Nếu item có badge (ví dụ số câu hỏi)
            if "badge" in item:
                badge_surf = assets.render_text(item["badge"], "xs", GRAY)
                clip_surf.blit(
                    badge_surf,
                    (self.rect.width - badge_surf.get_width() - 12,
                     item_y + (self.item_h - badge_surf.get_height()) // 2)
                )

        surface.blit(clip_surf, self.rect.topleft)

        # Viền danh sách
        pygame.draw.rect(surface, GRAY_DARK, self.rect, width=1, border_radius=8)

        # Scrollbar
        if self._max_scroll > 0:
            total_h = len(self.items) * self.item_h
            bar_h = max(30, int(self.rect.height ** 2 / total_h))
            bar_y = int(self.scroll_y / self._max_scroll * (self.rect.height - bar_h))
            bar_rect = pygame.Rect(
                self.rect.right - 8,
                self.rect.y + bar_y,
                6, bar_h
            )
            pygame.draw.rect(surface, CYAN_DIM, bar_rect, border_radius=3)

    def get_selected(self) -> list:
        """Trả về danh sách item đang được chọn."""
        return [it for it in self.items if it["id"] in self.selected_ids]


# === HELPER FUNCTIONS ===

def _lerp_color(c1, c2, t: float) -> tuple:
    """Nội suy tuyến tính giữa 2 màu RGB."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _scale_rect(rect: pygame.Rect, scale: float) -> pygame.Rect:
    """Scale rect quanh tâm."""
    cx, cy = rect.center
    w = int(rect.width * scale)
    h = int(rect.height * scale)
    return pygame.Rect(cx - w // 2, cy - h // 2, w, h)


def draw_title_bar(surface: pygame.Surface, title: str, subtitle: str = ""):
    """Vẽ thanh tiêu đề ở đầu màn hình."""
    # Nền gradient giả
    bar_h = 80
    bar_surf = pygame.Surface((surface.get_width(), bar_h), pygame.SRCALPHA)
    for y in range(bar_h):
        alpha = int(200 * (1 - y / bar_h))
        pygame.draw.line(bar_surf, (10, 20, 40, alpha), (0, y), (surface.get_width(), y))
    surface.blit(bar_surf, (0, 0))

    # Đường kẻ dưới
    pygame.draw.line(surface, CYAN_DIM, (0, bar_h), (surface.get_width(), bar_h), 1)

    # Tiêu đề
    t_surf = assets.render_text(title, "lg", CYAN, bold=True)
    surface.blit(t_surf, (40, (bar_h - t_surf.get_height()) // 2 - 6 if not subtitle else 10))

    if subtitle:
        s_surf = assets.render_text(subtitle, "xs", GRAY)
        surface.blit(s_surf, (40, 48))


def draw_crosshair(surface: pygame.Surface, x: int, y: int, size: int = 20, color=WHITE):
    """Vẽ tâm ngắm dạng dấu + với khoảng trống ở giữa."""
    gap = 6
    thickness = 2
    # Ngang
    pygame.draw.line(surface, color, (x - size, y), (x - gap, y), thickness)
    pygame.draw.line(surface, color, (x + gap, y), (x + size, y), thickness)
    # Dọc
    pygame.draw.line(surface, color, (x, y - size), (x, y - gap), thickness)
    pygame.draw.line(surface, color, (x, y + gap), (x, y + size), thickness)
    # Chấm giữa
    pygame.draw.circle(surface, color, (x, y), 2)
