"""
constants.py - Hằng số toàn cục của game
"""

import os

# === CỬA SỔ ===
SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
TITLE = "RoboLearn Shooter — Học & Chiến"

# === ĐƯỜNG DẪN ===
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SAVES_DIR = os.path.join(BASE_DIR, "saves")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

for _dir in [DATA_DIR, SAVES_DIR, ASSETS_DIR, FONTS_DIR]:
    os.makedirs(_dir, exist_ok=True)

# === FILE LƯU TRỮ ===
RANKING_FILE = os.path.join(SAVES_DIR, "ranking.json")
PROGRESS_FILE = os.path.join(SAVES_DIR, "progress.json")

# === MÀU SẮC ===
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_BG     = (10,  12,  20)
PANEL_BG    = (20,  25,  40)
PANEL_DARK  = (12,  15,  28)

CYAN        = (0,   220, 255)
CYAN_DIM    = (0,   140, 180)
ORANGE      = (255, 140, 0)
ORANGE_DIM  = (180, 90,  0)
RED         = (220, 50,  50)
RED_BRIGHT  = (255, 80,  80)
GREEN       = (50,  220, 100)
GREEN_DIM   = (30,  160, 70)
YELLOW      = (255, 220, 50)
PURPLE      = (160, 80,  220)
GRAY        = (120, 130, 150)
GRAY_DARK   = (50,  55,  70)
GRAY_LIGHT  = (180, 190, 210)

ZONE_HEAD   = (220, 80,  80)
ZONE_BODY   = (80,  160, 220)
ZONE_LIMB   = (80,  200, 120)

HP_HIGH     = (50,  200, 80)
HP_MED      = (220, 180, 50)
HP_LOW      = (220, 60,  60)

# === GAMEPLAY ===
ROBOT_MAX_HP    = 300
DAMAGE_HEAD     = 60
DAMAGE_BODY     = 40
DAMAGE_LIMB     = 20

MAX_WRONG_ANSWERS = 3   # ← Nâng lên 3 mạng

SCORE_HEAD  = 150
SCORE_BODY  = 100
SCORE_LIMB  = 50

# === LOẠI CÂU HỎI ===
Q_MULTIPLE_CHOICE = "multiple_choice"
Q_SHORT_ANSWER    = "short_answer"
Q_FACT_ANALYSIS   = "fact_analysis"

# === ĐỘ KHÓ / VÙNG ROBOT ===
ZONE_HEAD_KEY = "head"
ZONE_BODY_KEY = "body"
ZONE_LIMB_KEY = "limb"

ZONE_DIFFICULTY = {
    ZONE_HEAD_KEY: "hard",
    ZONE_BODY_KEY: "medium",
    ZONE_LIMB_KEY: "easy",
}

# === UI ===
BUTTON_H        = 52
BUTTON_RADIUS   = 10
ANIM_SPEED      = 4.0

# === FONT SIZE ===
FONT_XL   = 56
FONT_LG   = 36
FONT_MD   = 26
FONT_SM   = 20
FONT_XS   = 16

# === SCENE IDs ===
SCENE_MENU          = "menu"
SCENE_START         = "start"
SCENE_QUESTION_BANK = "question_bank"
SCENE_RANKING       = "ranking"
SCENE_GAMEPLAY      = "gameplay"
SCENE_RESULT        = "result"
SCENE_QUIT          = "quit"

# Multiplayer scene
SCENE_MULTIPLAYER   = "multiplayer"