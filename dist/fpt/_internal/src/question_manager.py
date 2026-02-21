"""
question_manager.py - Quản lý pool câu hỏi trong game
"""

import json
import random
import os
from src.constants import (
    Q_MULTIPLE_CHOICE, Q_SHORT_ANSWER, Q_FACT_ANALYSIS,
    ZONE_HEAD_KEY, ZONE_BODY_KEY, ZONE_LIMB_KEY,
    ZONE_DIFFICULTY,
)


class QuestionManager:
    """
    Pool câu hỏi trong phiên chơi.
    
    Phân loại theo difficulty:
    - hard   → zone head
    - medium → zone body  
    - easy   → zone limb
    """

    def __init__(self):
        # Dict: difficulty → list of questions
        self._pool = {
            "easy":   [],
            "medium": [],
            "hard":   [],
        }
        # Câu hỏi đã dùng trong vòng hiện tại
        self._used_ids = set()
        # Toàn bộ câu hỏi gốc (để reset)
        self._all_questions = []

    def load_files(self, filepaths: list) -> int:
        """
        Load danh sách file .json vào pool.
        Trả về tổng số câu hỏi đã load.
        """
        self._all_questions = []
        
        for fp in filepaths:
            if not os.path.isfile(fp):
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                questions = data.get("questions", [])
                self._all_questions.extend(questions)
            except Exception as e:
                print(f"[QuestionManager] Error loading {fp}: {e}")

        self._rebuild_pool()
        return len(self._all_questions)

    def _rebuild_pool(self):
        """Phân loại lại câu hỏi vào pool theo difficulty."""
        self._pool = {"easy": [], "medium": [], "hard": []}
        self._used_ids = set()

        for q in self._all_questions:
            diff = q.get("difficulty", "medium")
            if diff in self._pool:
                self._pool[diff].append(q)
            else:
                self._pool["medium"].append(q)

    def get_question_for_zone(self, zone: str) -> dict | None:
        """
        Lấy câu hỏi chưa dùng cho vùng robot.
        zone: ZONE_HEAD_KEY | ZONE_BODY_KEY | ZONE_LIMB_KEY
        
        Logic fallback:
        1. Lấy câu theo difficulty của zone
        2. Nếu hết → lấy bất kỳ difficulty còn câu
        3. Nếu tất cả đã dùng hết → reset pool rồi lấy lại
        """
        target_diff = ZONE_DIFFICULTY.get(zone, "medium")

        # Bước 1: Thử lấy đúng difficulty
        q = self._pick_from_difficulty(target_diff)
        if q:
            return q

        # Bước 2: Fallback sang difficulty khác
        for diff in ["hard", "medium", "easy"]:
            if diff == target_diff:
                continue
            q = self._pick_from_difficulty(diff)
            if q:
                return q

        # Bước 3: Đã hết tất cả → reset pool
        print("[QuestionManager] Pool exhausted, resetting...")
        self._rebuild_pool()
        q = self._pick_from_difficulty(target_diff)
        if q:
            return q

        # Không có câu hỏi nào
        return None

    def _pick_from_difficulty(self, difficulty: str) -> dict | None:
        """Chọn ngẫu nhiên 1 câu chưa dùng từ difficulty pool."""
        available = [
            q for q in self._pool.get(difficulty, [])
            if q["id"] not in self._used_ids
        ]
        if not available:
            return None

        q = random.choice(available)
        self._used_ids.add(q["id"])
        return q

    def get_stats(self) -> dict:
        """Thống kê pool câu hỏi."""
        used = len(self._used_ids)
        total = len(self._all_questions)
        return {
            "total": total,
            "used": used,
            "remaining": total - used,
            "by_difficulty": {
                diff: {
                    "total": len(qs),
                    "remaining": sum(1 for q in qs if q["id"] not in self._used_ids),
                }
                for diff, qs in self._pool.items()
            }
        }

    def check_answer(self, question: dict, user_answer) -> bool:
        """
        Kiểm tra đáp án.
        user_answer:
        - MC: str ("A"|"B"|"C"|"D")
        - SA: str (text)
        - FA: dict {"A": bool, "B": bool, "C": bool, "D": bool}
        """
        q_type = question["type"]
        correct = question["answer"]

        if q_type == Q_MULTIPLE_CHOICE:
            return str(user_answer).upper() == str(correct).upper()

        elif q_type == Q_SHORT_ANSWER:
            # So sánh case-insensitive, bỏ dấu cách thừa
            return str(user_answer).strip().lower() == str(correct).strip().lower()

        elif q_type == Q_FACT_ANALYSIS:
            if not isinstance(user_answer, dict):
                return False
            # Tất cả 4 nhận định đều phải đúng
            for key, expected_val in correct.items():
                if user_answer.get(key) != expected_val:
                    return False
            return True

        return False

    @property
    def has_questions(self) -> bool:
        """True nếu còn câu hỏi để dùng."""
        return len(self._all_questions) > 0
