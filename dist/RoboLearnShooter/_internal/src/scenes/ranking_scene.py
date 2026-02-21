"""
ranking_scene.py - Màn hình Bảng Xếp Hạng
============================================
Hiển thị top 20 người chơi, sắp xếp theo điểm.
"""

import pygame
import math
from src.scenes.base_scene import BaseScene
from src.constants import *
from src.assets import assets
from src.ui_components import Button, Panel, draw_title_bar
from src.ranking import RankingSystem


class RankingScene(BaseScene):
    """Bảng xếp hạng người chơi."""

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self._ranking = RankingSystem()
        self._entries = self._ranking.get_top(20)
        self._time = 0.0
        self._scroll = 0

        self._btn_back = Button(
            30, SCREEN_H - 65, 140, BUTTON_H, "← Quay lại",
            color_normal=GRAY, bg_hover=GRAY_DARK, font_size="sm"
        )
        self._btn_clear = Button(
            SCREEN_W - 200, SCREEN_H - 65, 170, BUTTON_H, "Xóa BXH",
            color_normal=RED, bg_hover=RED_BRIGHT, bg_normal=PANEL_BG,
            font_size="sm", icon="🗑"
        )
        self._confirm_clear = False
        self._confirm_timer = 0.0

    def update(self, dt: float, events: list):
        self._time += dt
        self._confirm_timer = max(0.0, self._confirm_timer - dt)

        self._btn_back.update(events, dt)
        self._btn_clear.update(events, dt)

        if self._btn_back.clicked:
            self.manager.go_to(SCENE_MENU)

        if self._btn_clear.clicked:
            if self._confirm_clear:
                self._ranking.clear()
                self._entries = []
                self._confirm_clear = False
            else:
                self._confirm_clear = True
                self._confirm_timer = 3.0

        if self._confirm_timer <= 0:
            self._confirm_clear = False

        # Scroll
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self._scroll = max(0, self._scroll - event.y)

    def draw(self):
        self.screen.fill(DARK_BG)
        draw_title_bar(self.screen, "BẢNG XẾP HẠNG", f"Top {len(self._entries)} người chơi")

        if not self._entries:
            empty = assets.render_text("Chưa có kết quả nào. Hãy chơi và lập kỷ lục!", "md", GRAY)
            self.screen.blit(empty, (SCREEN_W // 2 - empty.get_width() // 2, SCREEN_H // 2))
        else:
            self._draw_table()

        self._btn_back.draw(self.screen)

        # Clear button với xác nhận
        if self._confirm_clear:
            lbl = assets.render_text("Nhấn lại để xác nhận xóa!", "sm", RED)
            self.screen.blit(lbl, (SCREEN_W - 220 - lbl.get_width(), SCREEN_H - 105))
        self._btn_clear.draw(self.screen)

    def _draw_table(self):
        """Vẽ bảng xếp hạng."""
        headers = ["#", "Tên", "Điểm", "Đúng", "Sai", "Ngày"]
        col_x = [60, 120, 440, 580, 640, 720]
        col_w = [60, 320, 140, 60, 60, 200]

        # Header
        header_y = 105
        for i, (hdr, x) in enumerate(zip(headers, col_x)):
            hdr_surf = assets.render_text(hdr, "xs", CYAN, bold=True)
            self.screen.blit(hdr_surf, (x, header_y))

        pygame.draw.line(self.screen, CYAN_DIM, (40, 128), (SCREEN_W - 40, 128), 1)

        # Rows
        row_h = 46
        visible_rows = (SCREEN_H - 190) // row_h
        start = self._scroll

        for i, entry in enumerate(self._entries[start:start + visible_rows]):
            rank = start + i + 1
            row_y = 140 + i * row_h

            # Highlight top 3
            if rank == 1:
                row_color = (60, 50, 10)
                rank_color = YELLOW
            elif rank == 2:
                row_color = (40, 50, 60)
                rank_color = GRAY_LIGHT
            elif rank == 3:
                row_color = (50, 30, 20)
                rank_color = (205, 127, 50)
            else:
                row_color = PANEL_BG if i % 2 == 0 else PANEL_DARK
                rank_color = GRAY

            # Nền hàng
            row_surf = pygame.Surface((SCREEN_W - 80, row_h - 4), pygame.SRCALPHA)
            pygame.draw.rect(row_surf, (*row_color, 180), row_surf.get_rect(), border_radius=6)
            self.screen.blit(row_surf, (40, row_y))

            # Rank number (no medals, just numbers)
            rank_surf = assets.render_text(str(rank), "sm", rank_color, bold=(rank <= 3))
            self.screen.blit(rank_surf, (col_x[0], row_y + 12))

            # Tên
            # Highlight nếu là người chơi hiện tại
            is_current = (
                entry["name"].lower() == self.state.player_name.lower()
            )
            name_color = CYAN if is_current else WHITE
            name_surf = assets.render_text(entry["name"][:28], "sm", name_color,
                                           bold=is_current)
            self.screen.blit(name_surf, (col_x[1], row_y + 12))

            # Điểm (pulsing nếu rank 1)
            score_color = YELLOW if rank == 1 else WHITE
            score_surf = assets.render_text(str(entry["score"]), "sm", score_color,
                                            bold=(rank == 1))
            self.screen.blit(score_surf, (col_x[2], row_y + 12))

            # Đúng / Sai
            c_surf = assets.render_text(str(entry.get("correct", 0)), "sm", GREEN)
            self.screen.blit(c_surf, (col_x[3], row_y + 12))

            w_surf = assets.render_text(str(entry.get("wrong", 0)), "sm", RED)
            self.screen.blit(w_surf, (col_x[4], row_y + 12))

            # Ngày
            date_surf = assets.render_text(entry.get("date", ""), "xs", GRAY)
            self.screen.blit(date_surf, (col_x[5], row_y + 14))

        # Scrollbar hint
        if len(self._entries) > visible_rows:
            hint = assets.render_text("Cuộn để xem thêm ↕", "xs", GRAY)
            self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 105))