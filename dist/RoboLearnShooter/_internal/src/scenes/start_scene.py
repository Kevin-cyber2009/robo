"""
start_scene.py - Màn hình Bắt Đầu Game
"""

import pygame
import os
import json
from src.scenes.base_scene import BaseScene
from src.constants import *
from src.assets import assets
from src.ui_components import (
    Button, Panel, TextInput, ScrollList, draw_title_bar
)


class StartScene(BaseScene):
    """Nhập tên + chọn bộ câu hỏi trước khi chơi."""

    def __init__(self, screen, manager):
        super().__init__(screen, manager)

        # Skip name step for multiplayer
        if getattr(self.state, "multiplayer_mode", False):
            self._step = "class"
            self.state.player_name = "P1 & P2"  # Default name for multiplayer
        else:
            self._step = "name"
        
        self._selected_class = ""
        self._selected_subject = ""

        # UI
        self._name_input = TextInput(
            SCREEN_W // 2 - 220, 280, 440, 52,
            placeholder="Nhập tên của bạn..."
        )
        # Điền tên cũ nếu có
        if self.state.player_name and self._step == "name":
            self._name_input.text = self.state.player_name

        self._list = ScrollList(
            SCREEN_W // 2 - 300, 200, 600, 360,
            item_h=50, multi_select=False
        )
        self._file_list = ScrollList(
            SCREEN_W // 2 - 300, 200, 600, 360,
            item_h=50, multi_select=True
        )

        self._btn_next = Button(
            SCREEN_W // 2 - 160, 590, 150, BUTTON_H, "Tiếp →",
            font_size="md"
        )
        self._btn_back = Button(
            SCREEN_W // 2 + 20, 590, 150, BUTTON_H, "← Quay lại",
            color_normal=GRAY, bg_hover=GRAY_DARK, font_size="md"
        )
        self._btn_menu = Button(
            30, SCREEN_H - 65, 140, BUTTON_H, "Menu",
            color_normal=GRAY, bg_hover=GRAY_DARK, font_size="sm", icon="←"
        )
        self._btn_start = Button(
            SCREEN_W // 2 - 120, 590, 240, BUTTON_H, "Bắt Đầu Chiến!",
            color_normal=DARK_BG, bg_normal=ORANGE, bg_hover=YELLOW,
            font_size="md", icon=""
        )

        self._error_msg = ""
        self._error_timer = 0.0

        # Load danh sách lớp ngay nếu multiplayer (skip name step)
        if self._step == "class":
            self._load_classes()

    # ─── Data loading ────────────────────────────────────────────

    def _load_classes(self):
        items = []
        if os.path.isdir(DATA_DIR):
            for name in sorted(os.listdir(DATA_DIR)):
                path = os.path.join(DATA_DIR, name)
                if os.path.isdir(path):
                    subjects = [
                        s for s in os.listdir(path)
                        if os.path.isdir(os.path.join(path, s))
                    ]
                    items.append({
                        "id": name,
                        "text": f"{name}",
                        "badge": f"{len(subjects)} môn",
                    })
        self._list.set_items(items)

    def _load_subjects(self, class_name: str):
        items = []
        class_path = os.path.join(DATA_DIR, class_name)
        if os.path.isdir(class_path):
            for name in sorted(os.listdir(class_path)):
                path = os.path.join(class_path, name)
                if os.path.isdir(path):
                    n_files = len([
                        f for f in os.listdir(path) if f.endswith(".json")
                    ])
                    items.append({
                        "id": name,
                        "text": f"{name}",
                        "badge": f"{n_files} bộ đề",
                    })
        self._list.set_items(items)

    def _load_files(self, class_name: str, subject_name: str):
        items = []
        subject_path = os.path.join(DATA_DIR, class_name, subject_name)
        if os.path.isdir(subject_path):
            for fname in sorted(os.listdir(subject_path)):
                if fname.endswith(".json"):
                    fpath = os.path.join(subject_path, fname)
                    n_q = 0
                    try:
                        with open(fpath, encoding="utf-8") as f:
                            data = json.load(f)
                        n_q = len(data.get("questions", []))
                    except Exception:
                        pass
                    items.append({
                        "id": fpath,
                        "text": f"{fname[:-5]}",
                        "badge": f"{n_q} câu",
                    })
        self._file_list.set_items(items)

    # ─── Update ──────────────────────────────────────────────────

    def update(self, dt: float, events: list):
        self._error_timer = max(0.0, self._error_timer - dt)
        self._btn_menu.update(events, dt)
        if self._btn_menu.clicked:
            self.manager.go_to(SCENE_MENU)
            return

        if self._step == "name":
            self._update_name(dt, events)
        elif self._step == "class":
            self._update_class(dt, events)
        elif self._step == "subject":
            self._update_subject(dt, events)
        elif self._step == "files":
            self._update_files(dt, events)

    def _update_name(self, dt, events):
        self._name_input.update(events, dt)
        self._btn_next.update(events, dt)

        # Enter cũng chuyển bước
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self._proceed_from_name()

        if self._btn_next.clicked:
            self._proceed_from_name()

    def _proceed_from_name(self):
        name = self._name_input.value
        if not name:
            self._show_error("Vui lòng nhập tên của bạn!")
            return
        self.state.player_name = name
        self._step = "class"
        self._load_classes()

    def _update_class(self, dt, events):
        self._list.update(events)
        self._btn_next.update(events, dt)
        self._btn_back.update(events, dt)

        if self._btn_back.clicked:
            self._step = "name"

        if self._btn_next.clicked:
            sel = self._list.get_selected()
            if not sel:
                self._show_error("Chọn một lớp để tiếp tục!")
                return
            self._selected_class = sel[0]["id"]
            self._step = "subject"
            self._load_subjects(self._selected_class)

    def _update_subject(self, dt, events):
        self._list.update(events)
        self._btn_next.update(events, dt)
        self._btn_back.update(events, dt)

        if self._btn_back.clicked:
            self._step = "class"
            self._load_classes()

        if self._btn_next.clicked:
            sel = self._list.get_selected()
            if not sel:
                self._show_error("Chọn một môn để tiếp tục!")
                return
            self._selected_subject = sel[0]["id"]
            self._step = "files"
            self._load_files(self._selected_class, self._selected_subject)

    def _update_files(self, dt, events):
        self._file_list.update(events)
        self._btn_start.update(events, dt)
        self._btn_back.update(events, dt)

        if self._btn_back.clicked:
            self._step = "subject"
            self._load_subjects(self._selected_class)

        if self._btn_start.clicked:
            sel = self._file_list.get_selected()
            if not sel:
                self._show_error("Chọn ít nhất 1 bộ đề!")
                return
            self.state.selected_question_files = [it["id"] for it in sel]
            self.state.current_score = 0
            self.state.correct_count = 0
            self.state.wrong_count = 0
            self.state.answered_questions = []
            self.state.session_wrong = 0
            # Route theo mode
            if getattr(self.state, "multiplayer_mode", False):
                self.manager.go_to(SCENE_MULTIPLAYER)
            else:
                self.manager.go_to(SCENE_GAMEPLAY)

    def _show_error(self, msg: str):
        self._error_msg = msg
        self._error_timer = 3.0

    # ─── Draw ────────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(DARK_BG)

        # Tiêu đề & breadcrumb
        breadcrumbs = {
            "name":    "Bắt Đầu > Nhập Tên",
            "class":   f"Bắt Đầu > {self.state.player_name} > Chọn Lớp",
            "subject": f"Bắt Đầu > {self._selected_class} > Chọn Môn",
            "files":   f"Bắt Đầu > {self._selected_class} > {self._selected_subject} > Chọn Bộ Đề",
        }
        draw_title_bar(self.screen, "BẮT ĐẦU", breadcrumbs[self._step])

        # Multiplayer mode badge
        if getattr(self.state, "multiplayer_mode", False):
            import pygame as _pg
            badge_s = _pg.Surface((220, 32), _pg.SRCALPHA)
            _pg.draw.rect(badge_s, (255,100,60,60), badge_s.get_rect(), border_radius=8)
            _pg.draw.rect(badge_s, (255,100,60,180), badge_s.get_rect(), width=2, border_radius=8)
            self.screen.blit(badge_s, (SCREEN_W//2-110, 58))
            lbl = assets.render_text("CHẾ ĐỘ 2 NGƯỜI CHƠI", "xs", (255,140,80), bold=True)
            self.screen.blit(lbl, (SCREEN_W//2-lbl.get_width()//2, 66))

        if self._step == "name":
            self._draw_name()
        elif self._step in ("class", "subject"):
            self._draw_list()
        elif self._step == "files":
            self._draw_files()

        # Error message
        if self._error_timer > 0:
            alpha = min(255, int(self._error_timer * 120))
            err_surf = pygame.Surface((500, 44), pygame.SRCALPHA)
            pygame.draw.rect(err_surf, (*RED, alpha), err_surf.get_rect(), border_radius=8)
            txt = assets.render_text(self._error_msg, "sm", WHITE)
            err_surf.blit(txt, (12, 12))
            ex = SCREEN_W // 2 - 250
            ey = SCREEN_H - 120
            self.screen.blit(err_surf, (ex, ey))

        self._btn_menu.draw(self.screen)

    def _draw_name(self):
        # Panel trung tâm
        panel = Panel(SCREEN_W // 2 - 260, 200, 520, 200)
        panel.draw(self.screen)

        lbl = assets.render_text("Nhập tên của bạn:", "md", CYAN, bold=True)
        self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 220))

        self._name_input.draw(self.screen)

        hint = assets.render_text("Nhấn Enter hoặc nút Tiếp →", "xs", GRAY)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 350))

        self._btn_next.draw(self.screen)

    def _draw_list(self):
        step_labels = {
            "class":   ("Chọn Lớp", "Chọn lớp học chứa bộ câu hỏi của bạn"),
            "subject": ("Chọn Môn", f"Môn học trong lớp {self._selected_class}"),
        }
        title, sub = step_labels[self._step]

        lbl = assets.render_text(title, "lg", CYAN, bold=True)
        self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 115))

        sub_lbl = assets.render_text(sub, "sm", GRAY)
        self.screen.blit(sub_lbl, (SCREEN_W // 2 - sub_lbl.get_width() // 2, 158))

        if not self._list.items:
            no_data = assets.render_text("Chưa có dữ liệu. Vào 'Đẩy Câu Hỏi' để tạo.", "sm", GRAY)
            self.screen.blit(no_data, (SCREEN_W // 2 - no_data.get_width() // 2, 380))
        else:
            self._list.draw(self.screen)

        self._btn_next.draw(self.screen)
        self._btn_back.draw(self.screen)

    def _draw_files(self):
        lbl = assets.render_text("Chọn Bộ Đề", "lg", CYAN, bold=True)
        self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 115))

        sub = assets.render_text(
            f"Môn: {self._selected_subject}  |  Có thể chọn nhiều bộ đề", "sm", GRAY
        )
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 158))

        if not self._file_list.items:
            no_data = assets.render_text(
                "Chưa có bộ đề. Vào 'Đẩy Câu Hỏi' để upload .docx", "sm", GRAY
            )
            self.screen.blit(no_data, (SCREEN_W // 2 - no_data.get_width() // 2, 380))
        else:
            self._file_list.draw(self.screen)

        # Số đã chọn
        n_sel = len(self._file_list.selected_ids)
        if n_sel:
            info = assets.render_text(f"Đã chọn: {n_sel} bộ đề", "sm", GREEN)
            self.screen.blit(info, (SCREEN_W // 2 - info.get_width() // 2, 575))

        self._btn_start.draw(self.screen)
        self._btn_back.draw(self.screen)