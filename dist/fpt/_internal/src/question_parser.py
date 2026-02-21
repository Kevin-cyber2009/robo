"""
question_parser.py - Parser câu hỏi từ file .docx
===================================================
Hỗ trợ 3 định dạng câu hỏi:

=== ĐỊNH DẠNG 1: TRẮC NGHIỆM ===
[MC] [easy|medium|hard]
Câu hỏi: Nội dung câu hỏi...
A. Lựa chọn A
B. Lựa chọn B
C. Lựa chọn C
D. Lựa chọn D
Đáp án: A

=== ĐỊNH DẠNG 2: TRẢ LỜI NGẮN ===
[SA] [easy|medium|hard]
Câu hỏi: Nội dung câu hỏi...
Đáp án: câu trả lời

=== ĐỊNH DẠNG 3: PHÂN TÍCH DỮ KIỆN ===
[FA] [easy|medium|hard]
Dữ kiện: Đoạn văn dữ kiện...
A. Nhận định A
B. Nhận định B
C. Nhận định C
D. Nhận định D
Đáp án: A-Đúng,B-Sai,C-Đúng,D-Sai
"""

import re
import json
import uuid
from typing import Optional
from src.constants import Q_MULTIPLE_CHOICE, Q_SHORT_ANSWER, Q_FACT_ANALYSIS


class ParseError(Exception):
    """Lỗi khi parse câu hỏi không đúng định dạng."""
    pass


class QuestionParser:
    """
    Parse file .docx thành danh sách câu hỏi chuẩn hóa.
    
    Mỗi câu hỏi sau khi parse có dạng:
    {
        "id": str,           # UUID duy nhất
        "type": str,         # Q_MULTIPLE_CHOICE | Q_SHORT_ANSWER | Q_FACT_ANALYSIS
        "difficulty": str,   # "easy" | "medium" | "hard"
        "question": str,     # Nội dung câu hỏi
        "choices": dict,     # {"A": ..., "B": ..., "C": ..., "D": ...} (nếu có)
        "answer": str|dict,  # Đáp án
        "passage": str,      # Đoạn văn (FA only)
        "used": False,       # Đã được dùng chưa
    }
    """

    # Regex nhận dạng dòng header câu hỏi
    HEADER_PATTERN = re.compile(
        r"\[(MC|SA|FA)\]\s*\[(easy|medium|hard)\]",
        re.IGNORECASE
    )
    CHOICE_PATTERN = re.compile(r"^([A-D])[.\)]\s*(.+)$")
    ANSWER_PREFIX = re.compile(r"^(?:Đáp án|Dap an)\s*[:：]\s*", re.IGNORECASE)
    QUESTION_PREFIX = re.compile(r"^(?:Câu hỏi|Cau hoi|Question)\s*[:：]\s*", re.IGNORECASE)
    PASSAGE_PREFIX = re.compile(r"^(?:Dữ kiện|Du kien|Passage)\s*[:：]\s*", re.IGNORECASE)

    def parse_docx(self, filepath: str) -> list:
        """
        Parse file .docx, trả về list câu hỏi.
        Raise ParseError nếu file không hợp lệ.
        """
        try:
            from docx import Document
        except ImportError:
            raise ParseError("Thiếu thư viện python-docx. Cài bằng: pip install python-docx")

        try:
            doc = Document(filepath)
        except Exception as e:
            raise ParseError(f"Không thể mở file: {e}")

        # Lấy tất cả text lines (bỏ dòng trống đầu/cuối block)
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            lines.append(text)

        return self._parse_lines(lines, filepath)

    def _parse_lines(self, lines: list, source: str = "") -> list:
        """Chia lines thành các block câu hỏi rồi parse từng block."""
        # Tách blocks bằng header pattern
        blocks = []
        current_block = []

        for line in lines:
            if self.HEADER_PATTERN.match(line):
                if current_block:
                    blocks.append(current_block)
                current_block = [line]
            elif current_block:
                current_block.append(line)

        if current_block:
            blocks.append(current_block)

        if not blocks:
            raise ParseError(
                "Không tìm thấy câu hỏi nào. "
                "Mỗi câu phải bắt đầu bằng [MC]/[SA]/[FA] theo đúng định dạng."
            )

        questions = []
        errors = []
        for i, block in enumerate(blocks):
            try:
                q = self._parse_block(block)
                questions.append(q)
            except ParseError as e:
                errors.append(f"Block {i+1}: {e}")

        if errors and not questions:
            raise ParseError("Tất cả câu hỏi đều lỗi:\n" + "\n".join(errors))

        return questions, errors

    def _parse_block(self, lines: list) -> dict:
        """Parse một block câu hỏi."""
        # Dòng đầu tiên là header
        header = lines[0]
        m = self.HEADER_PATTERN.match(header)
        if not m:
            raise ParseError(f"Header không hợp lệ: '{header}'")

        q_type_raw = m.group(1).upper()
        difficulty = m.group(2).lower()

        type_map = {
            "MC": Q_MULTIPLE_CHOICE,
            "SA": Q_SHORT_ANSWER,
            "FA": Q_FACT_ANALYSIS,
        }
        q_type = type_map[q_type_raw]

        # Lấy nội dung còn lại
        content_lines = [l for l in lines[1:] if l.strip()]

        if q_type == Q_MULTIPLE_CHOICE:
            return self._parse_mc(content_lines, difficulty)
        elif q_type == Q_SHORT_ANSWER:
            return self._parse_sa(content_lines, difficulty)
        elif q_type == Q_FACT_ANALYSIS:
            return self._parse_fa(content_lines, difficulty)

    def _parse_mc(self, lines: list, difficulty: str) -> dict:
        """Parse trắc nghiệm 4 lựa chọn."""
        question_text = ""
        choices = {}
        answer = ""

        for line in lines:
            if self.ANSWER_PREFIX.match(line):
                answer = self.ANSWER_PREFIX.sub("", line).strip().upper()
            elif self.QUESTION_PREFIX.match(line):
                question_text = self.QUESTION_PREFIX.sub("", line).strip()
            elif self.CHOICE_PATTERN.match(line):
                m = self.CHOICE_PATTERN.match(line)
                choices[m.group(1).upper()] = m.group(2).strip()
            elif not choices and not question_text:
                # Dòng đầu tiên không có prefix → coi là câu hỏi
                question_text = line

        if not question_text:
            raise ParseError("Thiếu nội dung câu hỏi")
        if len(choices) != 4:
            raise ParseError(f"Cần đúng 4 lựa chọn A-D, tìm thấy: {list(choices.keys())}")
        if answer not in choices:
            raise ParseError(f"Đáp án '{answer}' không hợp lệ (phải là A/B/C/D)")

        return {
            "id": str(uuid.uuid4()),
            "type": Q_MULTIPLE_CHOICE,
            "difficulty": difficulty,
            "question": question_text,
            "choices": choices,
            "answer": answer,
            "passage": "",
            "used": False,
        }

    def _parse_sa(self, lines: list, difficulty: str) -> dict:
        """Parse câu trả lời ngắn."""
        question_text = ""
        answer = ""

        for line in lines:
            if self.ANSWER_PREFIX.match(line):
                answer = self.ANSWER_PREFIX.sub("", line).strip()
            elif self.QUESTION_PREFIX.match(line):
                question_text = self.QUESTION_PREFIX.sub("", line).strip()
            elif not question_text:
                question_text = line

        if not question_text:
            raise ParseError("Thiếu nội dung câu hỏi")
        if not answer:
            raise ParseError("Thiếu đáp án")

        return {
            "id": str(uuid.uuid4()),
            "type": Q_SHORT_ANSWER,
            "difficulty": difficulty,
            "question": question_text,
            "choices": {},
            "answer": answer.lower(),   # So sánh case-insensitive
            "passage": "",
            "used": False,
        }

    def _parse_fa(self, lines: list, difficulty: str) -> dict:
        """Parse phân tích dữ kiện (đúng/sai cho 4 nhận định)."""
        passage = ""
        choices = {}
        answer_raw = ""

        passage_lines = []
        reading_passage = False

        for line in lines:
            if self.ANSWER_PREFIX.match(line):
                answer_raw = self.ANSWER_PREFIX.sub("", line).strip()
                reading_passage = False
            elif self.PASSAGE_PREFIX.match(line):
                p = self.PASSAGE_PREFIX.sub("", line).strip()
                if p:
                    passage_lines.append(p)
                reading_passage = True
            elif self.CHOICE_PATTERN.match(line):
                reading_passage = False
                m = self.CHOICE_PATTERN.match(line)
                choices[m.group(1).upper()] = m.group(2).strip()
            elif reading_passage:
                passage_lines.append(line)

        passage = " ".join(passage_lines).strip()

        # Parse đáp án dạng: A-Đúng,B-Sai,C-Đúng,D-Sai
        answer_dict = {}
        if answer_raw:
            for part in answer_raw.split(","):
                part = part.strip()
                m = re.match(r"([A-D])[-\s]+(Đúng|Sai|True|False|Dung|true|false)", part, re.IGNORECASE)
                if m:
                    key = m.group(1).upper()
                    val = m.group(2).lower() in ("đúng", "true", "dung")
                    answer_dict[key] = val

        if not passage:
            raise ParseError("Thiếu dữ kiện (Dữ kiện: ...)")
        if len(choices) != 4:
            raise ParseError(f"Cần đúng 4 nhận định A-D")
        if len(answer_dict) != 4:
            raise ParseError(
                f"Đáp án FA phải có 4 mục. Ví dụ: A-Đúng,B-Sai,C-Đúng,D-Sai. "
                f"Tìm thấy: {answer_raw}"
            )

        return {
            "id": str(uuid.uuid4()),
            "type": Q_FACT_ANALYSIS,
            "difficulty": difficulty,
            "question": "Xác định đúng/sai cho các nhận định dưới đây:",
            "choices": choices,
            "answer": answer_dict,
            "passage": passage,
            "used": False,
        }

    def validate_file(self, filepath: str) -> tuple:
        """
        Kiểm tra file trước khi import.
        Trả về (is_valid: bool, message: str, questions: list)
        """
        try:
            questions, errors = self.parse_docx(filepath)
            msg = f"✓ Tìm thấy {len(questions)} câu hợp lệ"
            if errors:
                msg += f" ({len(errors)} câu lỗi bỏ qua)"
            return True, msg, questions
        except ParseError as e:
            return False, f"✗ Lỗi: {str(e)}", []
        except Exception as e:
            return False, f"✗ Lỗi không xác định: {str(e)}", []

    def save_questions(self, questions: list, filepath: str, metadata: dict = None):
        """Lưu câu hỏi đã parse sang file .json."""
        data = {
            "metadata": metadata or {},
            "questions": questions,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
