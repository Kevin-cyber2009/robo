"""
question_bank_scene.py - Màn hình Đẩy Câu Hỏi
"""

import pygame
import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog
from src.scenes.base_scene import BaseScene
from src.constants import *
from src.assets import assets
from src.ui_components import (
    Button, Panel, TextInput, ScrollList, draw_title_bar
)
from src.question_parser import QuestionParser, ParseError


class QuestionBankScene(BaseScene):
    """Màn hình quản lý ngân hàng câu hỏi."""

    STEP_CLASS = "class"
    STEP_SUBJECT = "subject"
    STEP_FILES = "files"

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self._parser = QuestionParser()
        self._step = self.STEP_CLASS

        self._selected_class = ""
        self._selected_subject = ""

        # === Danh sách lớp / môn ===
        self._list = ScrollList(
            60, 190, SCREEN_W - 400, 380, item_h=50
        )
        # === Danh sách file đã upload ===
        self._file_list = ScrollList(
            60, 190, SCREEN_W - 160, 340, item_h=50
        )

        # === Input tạo mới ===
        self._new_input = TextInput(
            60, 590, 340, 46, placeholder="Tên lớp / môn mới..."
        )
        self._btn_create = Button(410, 590, 140, 46, "Tạo Mới", font_size="sm", icon="+")

        # === Buttons điều hướng ===
        self._btn_back = Button(
            30, SCREEN_H - 65, 130, BUTTON_H, "← Quay lại",
            color_normal=GRAY, bg_hover=GRAY_DARK, font_size="sm"
        )
        self._btn_next = Button(
            SCREEN_W - 200, 590, 140, BUTTON_H, "Tiếp →", font_size="sm"
        )

        # Upload button (bước files)
        self._btn_upload = Button(
            SCREEN_W - 260, 190, 200, 46,
            "Upload .docx", bg_normal=ORANGE, bg_hover=YELLOW,
            color_normal=DARK_BG, font_size="sm", icon="📤"
        )
        self._btn_delete = Button(
            SCREEN_W - 260, 248, 200, 46,
            "Xóa đã chọn", bg_normal=RED, bg_hover=RED_BRIGHT,
            color_normal=WHITE, font_size="sm", icon="🗑"
        )

        # Status message (feedback)
        self._status_msg = ""
        self._status_color = GREEN
        self._status_timer = 0.0

        self._load_classes()

    # ─── Data ────────────────────────────────────────────────────

    def _load_classes(self):
        items = []
        if os.path.isdir(DATA_DIR):
            for name in sorted(os.listdir(DATA_DIR)):
                path = os.path.join(DATA_DIR, name)
                if os.path.isdir(path):
                    n_sub = sum(
                        1 for s in os.listdir(path)
                        if os.path.isdir(os.path.join(path, s))
                    )
                    items.append({"id": name, "text": f"📁 {name}", "badge": f"{n_sub} môn"})
        self._list.set_items(items)

    def _load_subjects(self):
        items = []
        class_path = os.path.join(DATA_DIR, self._selected_class)
        if os.path.isdir(class_path):
            for name in sorted(os.listdir(class_path)):
                path = os.path.join(class_path, name)
                if os.path.isdir(path):
                    n = len([f for f in os.listdir(path) if f.endswith(".json")])
                    items.append({"id": name, "text": f"📚 {name}", "badge": f"{n} bộ đề"})
        self._list.set_items(items)

    def _load_files(self):
        items = []
        subj_path = os.path.join(DATA_DIR, self._selected_class, self._selected_subject)
        if os.path.isdir(subj_path):
            for fname in sorted(os.listdir(subj_path)):
                if fname.endswith(".json"):
                    fpath = os.path.join(subj_path, fname)
                    n_q = 0
                    try:
                        with open(fpath, encoding="utf-8") as f:
                            data = json.load(f)
                        n_q = len(data.get("questions", []))
                    except Exception:
                        pass
                    items.append({
                        "id": fpath,
                        "text": f"📄 {fname[:-5]}",
                        "badge": f"{n_q} câu",
                    })
        self._file_list.set_items(items)

    # ─── Xử lý upload ────────────────────────────────────────────

    def _do_upload(self, src_path: str):
        """Validate + copy + parse file .docx."""
        src_path = src_path.strip().strip('"').strip("'")

        if not os.path.isfile(src_path):
            self._show_status(f"Không tìm thấy file: {src_path}", RED)
            return

        if not src_path.lower().endswith(".docx"):
            self._show_status("File phải có định dạng .docx!", RED)
            return

        # Validate
        valid, msg, questions = self._parser.validate_file(src_path)
        if not valid:
            self._show_status(msg, RED)
            return

        # Tên file output
        base_name = os.path.splitext(os.path.basename(src_path))[0]
        dest_dir = os.path.join(DATA_DIR, self._selected_class, self._selected_subject)
        os.makedirs(dest_dir, exist_ok=True)
        dest_json = os.path.join(dest_dir, base_name + ".json")

        # Lưu file JSON
        metadata = {
            "source_file": os.path.basename(src_path),
            "class": self._selected_class,
            "subject": self._selected_subject,
        }
        self._parser.save_questions(questions, dest_json, metadata)

        self._show_status(f"✓ Upload thành công! {msg}", GREEN)
        self._load_files()

    def _do_delete(self):
        """Xóa các file đã chọn."""
        selected = self._file_list.get_selected()
        if not selected:
            self._show_status("Chưa chọn file nào để xóa!", ORANGE)
            return
        for item in selected:
            try:
                os.remove(item["id"])
            except Exception as e:
                self._show_status(f"Lỗi xóa: {e}", RED)
                return
        self._show_status(f"Đã xóa {len(selected)} file!", GREEN)
        self._load_files()

    def _create_folder(self, step: str):
        name = self._new_input.value
        if not name:
            self._show_status("Nhập tên trước!", ORANGE)
            return

        # Sanitize tên folder
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-()").strip()
        if not safe_name:
            self._show_status("Tên không hợp lệ!", RED)
            return

        if step == self.STEP_CLASS:
            folder = os.path.join(DATA_DIR, safe_name)
        else:
            folder = os.path.join(DATA_DIR, self._selected_class, safe_name)

        os.makedirs(folder, exist_ok=True)
        self._new_input.clear()
        self._show_status(f"✓ Đã tạo: {safe_name}", GREEN)

        if step == self.STEP_CLASS:
            self._load_classes()
        else:
            self._load_subjects()

    def _show_status(self, msg: str, color=GREEN):
        self._status_msg = msg
        self._status_color = color
        self._status_timer = 4.0

    # ─── Update ──────────────────────────────────────────────────

    def update(self, dt: float, events: list):
        self._status_timer = max(0.0, self._status_timer - dt)

        self._btn_back.update(events, dt)
        if self._btn_back.clicked:
            if self._step == self.STEP_CLASS:
                self.manager.go_to(SCENE_MENU)
            elif self._step == self.STEP_SUBJECT:
                self._step = self.STEP_CLASS
                self._load_classes()
            elif self._step == self.STEP_FILES:
                self._step = self.STEP_SUBJECT
                self._load_subjects()
            return

        if self._step == self.STEP_CLASS:
            self._update_class(dt, events)
        elif self._step == self.STEP_SUBJECT:
            self._update_subject(dt, events)
        elif self._step == self.STEP_FILES:
            self._update_files(dt, events)

    def _update_class(self, dt, events):
        self._list.update(events)
        self._new_input.update(events, dt)
        self._btn_create.update(events, dt)
        self._btn_next.update(events, dt)

        if self._btn_create.clicked:
            self._create_folder(self.STEP_CLASS)

        if self._btn_next.clicked:
            sel = self._list.get_selected()
            if not sel:
                self._show_status("Chọn lớp để tiếp tục!", ORANGE)
                return
            self._selected_class = sel[0]["id"]
            self._step = self.STEP_SUBJECT
            self._load_subjects()

    def _update_subject(self, dt, events):
        self._list.update(events)
        self._new_input.update(events, dt)
        self._btn_create.update(events, dt)
        self._btn_next.update(events, dt)

        if self._btn_create.clicked:
            self._create_folder(self.STEP_SUBJECT)

        if self._btn_next.clicked:
            sel = self._list.get_selected()
            if not sel:
                self._show_status("Chọn môn để tiếp tục!", ORANGE)
                return
            self._selected_subject = sel[0]["id"]
            self._step = self.STEP_FILES
            self._load_files()

    def _update_files(self, dt, events):
        self._file_list.update(events)
        self._btn_upload.update(events, dt)
        self._btn_delete.update(events, dt)

        if self._btn_upload.clicked:
            self._open_file_dialog()

        if self._btn_delete.clicked:
            self._do_delete()

    def _open_file_dialog(self):
        """Mở cửa sổ chọn file .docx của hệ điều hành."""
        root = tk.Tk()
        root.withdraw()                   # Ẩn cửa sổ tkinter chính
        root.attributes("-topmost", True) # Hiện trên cửa sổ pygame
        file_path = filedialog.askopenfilename(
            title="Chọn file .docx để upload",
            filetypes=[("Word Document", "*.docx"), ("Tất cả file", "*.*")]
        )
        root.destroy()

        if file_path:
            self._do_upload(file_path)

    # ─── Draw ────────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(DARK_BG)

        breadcrumb = {
            self.STEP_CLASS:   "Đẩy Câu Hỏi > Chọn Lớp",
            self.STEP_SUBJECT: f"Đẩy Câu Hỏi > {self._selected_class} > Chọn Môn",
            self.STEP_FILES:   f"Đẩy Câu Hỏi > {self._selected_class} > {self._selected_subject}",
        }
        draw_title_bar(self.screen, "ĐẨY CÂU HỎI", breadcrumb[self._step])

        if self._step in (self.STEP_CLASS, self.STEP_SUBJECT):
            self._draw_folder_step()
        elif self._step == self.STEP_FILES:
            self._draw_files_step()

        # Status message
        if self._status_timer > 0:
            self._draw_status()

        self._btn_back.draw(self.screen)

    def _draw_folder_step(self):
        is_class = (self._step == self.STEP_CLASS)
        title = "Chọn hoặc tạo Lớp" if is_class else f"Chọn hoặc tạo Môn ({self._selected_class})"
        lbl = assets.render_text(title, "md", CYAN, bold=True)
        self.screen.blit(lbl, (60, 110))

        self._list.draw(self.screen)
        self._new_input.draw(self.screen)
        self._btn_create.draw(self.screen)
        self._btn_next.draw(self.screen)

    def _draw_files_step(self):
        lbl = assets.render_text(
            f"Bộ đề trong: {self._selected_class} / {self._selected_subject}",
            "md", CYAN, bold=True
        )
        self.screen.blit(lbl, (60, 110))

        # Hướng dẫn định dạng
        guide_lines = [
            "📋 Định dạng .docx:",
            "  [MC] [easy/medium/hard]  ← Trắc nghiệm",
            "  [SA] [easy/medium/hard]  ← Trả lời ngắn",
            "  [FA] [easy/medium/hard]  ← Phân tích dữ kiện",
        ]
        guide_x = SCREEN_W - 340
        guide_y = 560
        for i, line in enumerate(guide_lines):
            color = CYAN if i == 0 else GRAY
            txt = assets.render_text(line, "xs", color)
            self.screen.blit(txt, (guide_x, guide_y + i * 20))

        self._file_list.draw(self.screen)
        self._btn_upload.draw(self.screen)
        self._btn_delete.draw(self.screen)

        # Số file
        n = len(self._file_list.items)
        info = assets.render_text(f"Tổng: {n} bộ đề", "xs", GRAY)
        self.screen.blit(info, (60, 545))

    def _draw_status(self):
        alpha = min(255, int(self._status_timer * 80))
        w = min(700, assets.font("sm").size(self._status_msg)[0] + 30)
        surf = pygame.Surface((w, 40), pygame.SRCALPHA)
        bg_color = (*self._status_color, min(160, alpha))
        pygame.draw.rect(surf, bg_color, surf.get_rect(), border_radius=8)
        txt = assets.render_text(self._status_msg, "sm", WHITE)
        surf.blit(txt, (10, (40 - txt.get_height()) // 2))
        self.screen.blit(surf, (60, SCREEN_H - 80))