"""
base_scene.py - Lớp cơ sở cho tất cả Scene
"""


class BaseScene:

    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager  # GameManager để gọi go_to()
        self.state = manager.state  # GameState dùng chung

    def update(self, dt: float, events: list):
        """Cập nhật logic. Override trong subclass."""
        pass

    def draw(self):
        """Vẽ màn hình. Override trong subclass."""
        pass
