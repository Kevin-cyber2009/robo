import sys
import os

# Thêm thư mục gốc vào sys.path để import module nội bộ
sys.path.insert(0, os.path.dirname(__file__))

import pygame
from src.constants import SCREEN_W, SCREEN_H, FPS, TITLE
from src.game_manager import GameManager


def main():
    """Hàm khởi động chính của game."""
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption(TITLE)

    # Khởi tạo cửa sổ game
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    # GameManager điều phối tất cả các màn hình (scene)
    manager = GameManager(screen)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  

        # Thu thập sự kiện
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # Cập nhật + vẽ scene hiện tại
        manager.update(dt, events)
        manager.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
