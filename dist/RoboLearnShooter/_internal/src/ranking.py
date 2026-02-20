"""
ranking.py - Hệ thống Bảng Xếp Hạng.
"""

import json
import os
from datetime import datetime
from src.constants import RANKING_FILE


class RankingSystem:
    """Quản lý lưu và đọc bảng xếp hạng."""

    MAX_ENTRIES = 100   # Giữ tối đa 100 kết quả

    def __init__(self):
        self._entries = []
        self._load()

    def _load(self):
        """Đọc file ranking."""
        if not os.path.isfile(RANKING_FILE):
            self._entries = []
            return
        try:
            with open(RANKING_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self._entries = data.get("rankings", [])
        except Exception as e:
            print(f"[Ranking] Load error: {e}")
            self._entries = []

    def _save(self):
        """Ghi file ranking."""
        try:
            os.makedirs(os.path.dirname(RANKING_FILE), exist_ok=True)
            with open(RANKING_FILE, "w", encoding="utf-8") as f:
                json.dump({"rankings": self._entries}, f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Ranking] Save error: {e}")

    def add_entry(
        self,
        player_name: str,
        score: int,
        correct: int,
        wrong: int,
        question_count: int = 0,
    ) -> int:
        """
        Thêm kết quả mới.
        Trả về rank (thứ hạng 1-based) sau khi thêm.
        """
        entry = {
            "name": player_name,
            "score": score,
            "correct": correct,
            "wrong": wrong,
            "total": question_count,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        self._entries.append(entry)
        # Sắp xếp: điểm cao nhất trước
        self._entries.sort(key=lambda e: e["score"], reverse=True)
        # Giữ top MAX_ENTRIES
        self._entries = self._entries[:self.MAX_ENTRIES]
        self._save()

        # Tìm rank
        for i, e in enumerate(self._entries):
            if (e["name"] == player_name and
                    e["score"] == score and
                    e["date"] == entry["date"]):
                return i + 1
        return len(self._entries)

    def get_top(self, n: int = 20) -> list:
        """Lấy top N kết quả."""
        return self._entries[:n]

    def get_all(self) -> list:
        return self._entries.copy()

    def get_player_best(self, player_name: str) -> dict | None:
        """Lấy điểm cao nhất của người chơi."""
        for entry in self._entries:
            if entry["name"].lower() == player_name.lower():
                return entry
        return None

    def clear(self):
        """Xóa toàn bộ ranking."""
        self._entries = []
        self._save()
