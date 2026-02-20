"""
menu_scene.py - Màn hình Menu Chính
"""

import pygame
import math
import random
from src.scenes.base_scene import BaseScene
from src.constants import *
from src.assets import assets
from src.ui_components import Button


class MenuScene(BaseScene):
    """Menu chính với hiệu ứng nền particle."""

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self._build_buttons()
        self._init_particles()
        self._time = 0.0
        self._title_y = -100     # Title bay vào từ trên
        self._buttons_alpha = 0  # Buttons fade in

    def _build_buttons(self):
        cx = SCREEN_W // 2
        btn_w = 340
        btn_half = 165
        start_y = 240
        gap = 65

        # 2 nút chơi đơn cạnh nhau (có/không countdown)
        self.buttons = [
            Button(cx - btn_half - 5, start_y, btn_half, BUTTON_H,
                   "Time Attack",  CYAN,   DARK_BG, PANEL_BG, (255,180,0), "sm", None),
            Button(cx + 5,            start_y, btn_half, BUTTON_H,
                   "Thường",       CYAN,   DARK_BG, PANEL_BG, CYAN,        "sm", None),
            Button(cx - btn_w // 2, start_y + 1 * gap, btn_w, BUTTON_H,
                   "2 Người Chơi",   CYAN, DARK_BG,  PANEL_BG, ORANGE,  "md", ""),
            Button(cx - btn_w // 2, start_y + 2 * gap, btn_w, BUTTON_H,
                   "Đẩy Câu Hỏi",   CYAN, DARK_BG,  PANEL_BG, ORANGE,  "md", ""),
            Button(cx - btn_w // 2, start_y + 3 * gap, btn_w, BUTTON_H,
                   "Bảng Xếp Hạng", CYAN, DARK_BG,  PANEL_BG, YELLOW,  "md", ""),
            Button(cx - btn_w // 2, start_y + 4 * gap, btn_w, BUTTON_H,
                   "Thoát",         GRAY, DARK_BG,   PANEL_BG, RED,     "md", ""),
        ]
        # Targets: "start_countdown" | "start_normal" | "start_multi" | scene_id
        self.btn_targets = [
            "start_countdown", "start_normal",
            "start_multi",
            SCENE_QUESTION_BANK, SCENE_RANKING, SCENE_QUIT
        ]

    def _init_particles(self):
        """Khởi tạo particle ngôi sao nền."""
        self.particles = []
        for _ in range(80):
            self.particles.append({
                "x": random.uniform(0, SCREEN_W),
                "y": random.uniform(0, SCREEN_H),
                "speed": random.uniform(10, 40),
                "size": random.uniform(1, 3),
                "alpha": random.randint(60, 200),
                "flicker": random.uniform(0, math.pi * 2),
            })

    def update(self, dt: float, events: list):
        self._time += dt

        # Intro animation
        target_title_y = 80
        self._title_y += (target_title_y - self._title_y) * min(dt * 5, 1.0)
        self._buttons_alpha = min(255, self._buttons_alpha + int(dt * 400))

        # Cập nhật particle
        for p in self.particles:
            p["y"] += p["speed"] * dt
            if p["y"] > SCREEN_H:
                p["y"] = -5
                p["x"] = random.uniform(0, SCREEN_W)
            p["flicker"] += dt * 2

        # Cập nhật buttons + xử lý click
        for i, btn in enumerate(self.buttons):
            if btn.update(events, dt):
                target = self.btn_targets[i]
                if target == "start_countdown":
                    self.manager.state.multiplayer_mode = False
                    self.manager.state.countdown_mode = True
                    self.manager.go_to(SCENE_START)
                elif target == "start_normal":
                    self.manager.state.multiplayer_mode = False
                    self.manager.state.countdown_mode = False
                    self.manager.go_to(SCENE_START)
                elif target == "start_multi":
                    self.manager.state.multiplayer_mode = True
                    self.manager.state.countdown_mode = False
                    self.manager.go_to(SCENE_START)
                else:
                    self.manager.state.multiplayer_mode = False
                    self.manager.go_to(target)

    def draw(self):
        surf = self.screen

        # === NỀN TỐI ===
        surf.fill(DARK_BG)
        self._draw_grid(surf)
        self._draw_particles(surf)

        # === LOGO / TIÊU ĐỀ ===
        self._draw_title(surf)

   

        for btn in self.buttons:
            btn.draw(surf)

      

    def _draw_grid(self, surf: pygame.Surface):
        """Lưới nền theo phong cách sci-fi."""
        grid_color = (20, 30, 50)
        step = 60
        for x in range(0, SCREEN_W, step):
            pygame.draw.line(surf, grid_color, (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, step):
            pygame.draw.line(surf, grid_color, (0, y), (SCREEN_W, y))

        # Đường ngang sáng ở giữa (hiệu ứng horizon)
        glow_y = SCREEN_H // 2
        for i in range(3):
            alpha = 40 - i * 12
            line_surf = pygame.Surface((SCREEN_W, 1), pygame.SRCALPHA)
            pygame.draw.line(line_surf, (*CYAN, alpha), (0, 0), (SCREEN_W, 0))
            surf.blit(line_surf, (0, glow_y + i))
            surf.blit(line_surf, (0, glow_y - i))

    def _draw_particles(self, surf: pygame.Surface):
        for p in self.particles:
            alpha = int(p["alpha"] * (0.6 + 0.4 * math.sin(p["flicker"])))
            size = p["size"]
            s = pygame.Surface((int(size * 2 + 2), int(size * 2 + 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*WHITE, alpha), (int(size + 1), int(size + 1)), int(size))
            surf.blit(s, (int(p["x"]), int(p["y"])))

    def _draw_title(self, surf: pygame.Surface):
        # Pulse animation tiêu đề
        pulse = math.sin(self._time * 2) * 0.03 + 1.0

        # Shadow
        shadow = assets.render_text("ROBOLEARN", "xl", (0, 100, 140), bold=True)
        cx = SCREEN_W // 2
        ty = int(self._title_y)
        surf.blit(shadow, (cx - shadow.get_width() // 2 + 3, ty + 3))

        # Main title
        title = assets.render_text("ROBOLEARN", "xl", CYAN, bold=True)
        # Nhẹ nhàng scale bằng transform
        w = int(title.get_width() * pulse)
        h = int(title.get_height() * pulse)
        scaled = pygame.transform.scale(title, (w, h))
        surf.blit(scaled, (cx - w // 2, ty - (h - title.get_height()) // 2))

        # Subtitle
        sub = assets.render_text("SHOOTER", "lg", ORANGE, bold=True)
        surf.blit(sub, (cx - sub.get_width() // 2, ty + title.get_height() + 4))

        # Tagline
        tag = assets.render_text(
            "Học - Chiến - Chinh Phục", "sm", GRAY_LIGHT
        )
        surf.blit(tag, (cx - tag.get_width() // 2, ty + title.get_height() + 50))

        # Đường trang trí dưới tiêu đề
        bar_w = 200
        bar_x = cx - bar_w // 2
        bar_y = ty + title.get_height() + 82
        pygame.draw.rect(surf, CYAN_DIM, (bar_x, bar_y, bar_w, 2), border_radius=1)
