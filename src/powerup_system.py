"""
powerup_system.py - Hệ thống Power-up thả từ robot khi bắn trúng
"""
import pygame, math, random
from src.constants import *
from src.assets import assets

# ── Định nghĩa power-up ────────────────────────────────────────
POWERUP_DEFS = {
    "heal":         {"icon":"",  "color":(220,60,80),   "label":"HEAL",         "weight":15},
    "shield":       {"icon":"",  "color":(80,160,255),  "label":"SHIELD",       "weight":20},
    "double_score": {"icon":"",  "color":(255,210,40),  "label":"×2 SCORE",     "weight":20},
    "slow_time":    {"icon":"",  "color":(60,220,255),  "label":"SLOW TIME",    "weight":20},
    "hint":         {"icon":"", "color":(255,200,60),  "label":"HINT",         "weight":25},
}

DROP_CHANCE = 0.35   # 35% robot thả item khi bị hit

class FloatingItem:
    """Item bay lơ lửng trên màn hình."""
    def __init__(self, x, y, kind):
        self.x      = float(x)
        self.y      = float(y)
        self.kind   = kind
        self.life   = 6.0      # Biến mất sau 6 giây
        self.base_y = float(y)
        self.phase  = random.uniform(0, math.pi*2)
        self.vx     = random.uniform(-1.2, 1.2)
        self.vy     = random.uniform(-2.5, -1.5)
        self.radius = 28
        self.collected = False
        self._sparkles = [{"angle":random.uniform(0,math.pi*2),"r":random.uniform(20,40),"phase":random.random()*6} for _ in range(6)]

    def update(self, dt):
        self.life -= dt
        self.x    += self.vx * dt * 30
        self.vy   += 1.5 * dt           # Nhẹ hấp dẫn
        self.vy   *= 0.98
        self.y    += self.vy * dt * 30
        self.vx   *= 0.99
        # Lơ lửng sau khi ổn định
        if abs(self.vy) < 0.5:
            self.y = self.base_y + math.sin(pygame.time.get_ticks()*0.002 + self.phase) * 8

    def check_click(self, mx, my) -> bool:
        return math.hypot(mx - self.x, my - self.y) <= self.radius + 10

    def draw(self, surf, t):
        if self.collected or self.life <= 0: return
        d    = POWERUP_DEFS[self.kind]
        color= d["color"]
        r    = self.radius

        # Fade out khi gần hết
        alpha = min(255, int(self.life / 6.0 * 255)) if self.life < 1.5 else 255

        # Sparkles vòng ngoài
        for sp in self._sparkles:
            sa = int(alpha * 0.6)
            if sa < 5: continue
            sx = self.x + math.cos(sp["angle"] + t*1.5) * sp["r"]
            sy = self.y + math.sin(sp["angle"] + t*1.5) * sp["r"] * 0.5
            gs = pygame.Surface((8,8), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*color, sa), (4,4), 4)
            surf.blit(gs, (int(sx)-4, int(sy)-4))

        # Glow hào quang
        glow_r = int(r * 1.8)
        gs = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*color, int(alpha*0.25)), (glow_r,glow_r), glow_r)
        surf.blit(gs, (int(self.x)-glow_r, int(self.y)-glow_r))

        # Nền vòng tròn
        bg_s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(bg_s, (10,14,28,int(alpha*0.9)), (r+2,r+2), r+2)
        surf.blit(bg_s, (int(self.x)-r-2, int(self.y)-r-2))

        # Viền neon
        c_s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(c_s, (*color, alpha), (r+2,r+2), r+2, 3)
        surf.blit(c_s, (int(self.x)-r-2, int(self.y)-r-2))

        # Icon
        ic = assets.render_text(d["icon"], "md", color)
        surf.blit(ic, (int(self.x)-ic.get_width()//2, int(self.y)-ic.get_height()//2))

        # Label phía dưới
        lbl = assets.render_text(d["label"], "xs", color, bold=True)
        surf.blit(lbl, (int(self.x)-lbl.get_width()//2, int(self.y)+r+3))


class PowerupSystem:
    """Quản lý tất cả floating items trên màn hình."""

    def __init__(self):
        self._items: list[FloatingItem] = []
        self._active: dict = {
            "shield": False,
            "double_score": 0.0,   # Thời gian còn lại
            "slow_time": False,    # Chỉ áp dụng 1 câu
            "hint": False,         # Chỉ áp dụng 1 câu
        }
        self._collected_log: list = []  # Log thông báo thu thập
        self._notifs: list = []   # [(text, color, life, y)]

    # ── Spawn ─────────────────────────────────────────────────

    def maybe_drop(self, robot_cx, robot_cy):
        """Gọi khi robot bị bắn trúng. Có chance thả item."""
        if random.random() > DROP_CHANCE: return
        kinds  = list(POWERUP_DEFS.keys())
        weights= [POWERUP_DEFS[k]["weight"] for k in kinds]
        kind   = random.choices(kinds, weights=weights, k=1)[0]
        x = robot_cx + random.randint(-80, 80)
        y = robot_cy + random.randint(-60, 20)
        self._items.append(FloatingItem(x, y, kind))

    # ── Update ────────────────────────────────────────────────

    def update(self, dt, events):
        """Trả về list kind vừa được collect."""
        collected = []
        # Timer double score
        if self._active["double_score"] > 0:
            self._active["double_score"] = max(0.0, self._active["double_score"] - dt)

        # Items
        for item in self._items[:]:
            item.update(dt)
            if item.life <= 0 or item.collected:
                self._items.remove(item)

        # Click để collect
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for item in self._items[:]:
                    if not item.collected and item.check_click(mx, my):
                        item.collected = True
                        self._apply(item.kind)
                        collected.append(item.kind)
                        break

        # Notifs
        for n in self._notifs[:]:
            n["life"] -= dt
            n["y"] -= dt * 30
            if n["life"] <= 0: self._notifs.remove(n)

        return collected

    def _apply(self, kind):
        d = POWERUP_DEFS[kind]
        if kind == "double_score":
            self._active["double_score"] = 30.0
        elif kind in ("slow_time", "hint", "shield"):
            self._active[kind] = True
        # Notif
        self._notifs.append({"text": f"+  {d['label']}!", "color": d["color"],
                              "life": 2.2, "y": float(SCREEN_H//2 - 80)})

    # ── Consume (gọi khi dùng) ────────────────────────────────

    def consume_shield(self) -> bool:
        if self._active["shield"]:
            self._active["shield"] = False; return True
        return False

    def consume_slow_time(self) -> bool:
        if self._active["slow_time"]:
            self._active["slow_time"] = False; return True
        return False

    def consume_hint(self) -> bool:
        if self._active["hint"]:
            self._active["hint"] = False; return True
        return False

    def consume_heal(self) -> bool:
        """Trả True nếu có heal item. Gọi từ gameplay khi nhặt."""
        return False  # Heal áp dụng ngay, không cần consume

    # ── Getters ───────────────────────────────────────────────

    @property
    def has_shield(self): return self._active["shield"]

    @property
    def has_slow_time(self): return self._active["slow_time"]

    @property
    def has_hint(self): return self._active["hint"]

    @property
    def double_score_active(self): return self._active["double_score"] > 0

    @property
    def double_score_remaining(self): return self._active["double_score"]

    # ── Draw ──────────────────────────────────────────────────

    def draw(self, surf, t):
        for item in self._items:
            item.draw(surf, t)
        # Notifs
        for n in self._notifs:
            a = min(255, int(n["life"]/2.2 * 255))
            ns = assets.render_text(n["text"], "lg", (*n["color"],), bold=True, shadow=True)
            ns.set_alpha(a)
            surf.blit(ns, (SCREEN_W//2 - ns.get_width()//2, int(n["y"])))

    def draw_hud(self, surf):
        """Vẽ active buffs ở góc trái dưới."""
        x = 10; y = SCREEN_H - 44
        if self._active["shield"]:
            self._draw_buff(surf, x, y, "", "SHIELD", (80,160,255)); x += 90
        if self._active["double_score"] > 0:
            t = self._active["double_score"]
            self._draw_buff(surf, x, y, "", f"×2  {t:.0f}s", (255,210,40)); x += 100
        if self._active["slow_time"]:
            self._draw_buff(surf, x, y, "", "SLOW", (60,220,255)); x += 80
        if self._active["hint"]:
            self._draw_buff(surf, x, y, "", "HINT", (255,200,60)); x += 80

    def _draw_buff(self, surf, x, y, icon, label, color):
        bg = pygame.Surface((88, 36), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*color, 30), bg.get_rect(), border_radius=8)
        pygame.draw.rect(bg, (*color, 120), bg.get_rect(), width=1, border_radius=8)
        surf.blit(bg, (x, y))
        ic = assets.render_text(icon, "sm", color)
        surf.blit(ic, (x+6, y+(36-ic.get_height())//2))
        lb = assets.render_text(label, "xs", color, bold=True)
        surf.blit(lb, (x+30, y+(36-lb.get_height())//2))