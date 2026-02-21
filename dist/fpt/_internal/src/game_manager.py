"""
game_manager.py - Điều phối Scene (Màn hình)
"""

import pygame
from src.constants import *


class GameState:
    """Trạng thái chia sẻ giữa các scene."""
    def __init__(self):
        self.player_name: str = ""
        self.selected_question_files: list = []    # Danh sách file .json đã chọn
        self.current_score: int = 0
        self.correct_count: int = 0
        self.wrong_count: int = 0
        self.answered_questions: list = []         # Lịch sử câu đã làm
        self.session_wrong: int = 0                # Sai trong phiên hiện tại
        self.combo_max: int = 0                    # Combo cao nhất trong game
        self.multiplayer_mode: bool = False        # True = 2 người chơi
        self.countdown_mode: bool = False          # True = Time Attack (có đếm ngược)


class GameManager:

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.state = GameState()
        self._current_scene = None
        self._pending_scene = None

        # Import lazy để tránh circular import
        self.go_to(SCENE_MENU)

    def go_to(self, scene_id: str, **kwargs):
        """Chuyển đến scene mới. kwargs truyền thêm context."""
        self._pending_scene = (scene_id, kwargs)

    def _create_scene(self, scene_id: str, kwargs: dict):
        """Factory tạo scene theo ID."""
        # Import ở đây để tránh circular import khi khởi tạo
        if scene_id == SCENE_MENU:
            from src.scenes.menu_scene import MenuScene
            return MenuScene(self.screen, self)

        elif scene_id == SCENE_START:
            from src.scenes.start_scene import StartScene
            return StartScene(self.screen, self)

        elif scene_id == SCENE_QUESTION_BANK:
            from src.scenes.question_bank_scene import QuestionBankScene
            return QuestionBankScene(self.screen, self)

        elif scene_id == SCENE_RANKING:
            from src.scenes.ranking_scene import RankingScene
            return RankingScene(self.screen, self)

        elif scene_id == SCENE_GAMEPLAY:
            from src.scenes.gameplay_scene import GameplayScene
            return GameplayScene(self.screen, self)

        elif scene_id == SCENE_RESULT:
            from src.scenes.result_scene import ResultScene
            return ResultScene(self.screen, self)

        elif scene_id == SCENE_MULTIPLAYER:
            from src.scenes.multiplayer_scene import MultiplayerScene
            return MultiplayerScene(self.screen, self)

        else:
            raise ValueError(f"Unknown scene: {scene_id}")

    def update(self, dt: float, events: list):
        """Cập nhật scene hiện tại + xử lý chuyển scene."""
        # Xử lý pending scene transition
        if self._pending_scene is not None:
            scene_id, kwargs = self._pending_scene
            self._pending_scene = None
            if scene_id == SCENE_QUIT:
                import sys
                pygame.quit()
                sys.exit()
            self._current_scene = self._create_scene(scene_id, kwargs)

        if self._current_scene:
            self._current_scene.update(dt, events)

    def draw(self):
        """Vẽ scene hiện tại."""
        self.screen.fill(DARK_BG)
        if self._current_scene:
            self._current_scene.draw()