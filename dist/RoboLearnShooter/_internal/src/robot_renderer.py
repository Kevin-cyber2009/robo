"""
robot_renderer.py - 7 CINEMATIC Robot Designs :)))))
"""

import pygame
import math
import random
from src.constants import *


#   PALETTE 

ROBOT_PALETTES = [
    # 0 GRUNT
    {
        "name": "GRUNT",
        "title": "Lính Sắt",
        "head":  (40,  120, 60),
        "body":  (30,  100, 50),
        "limb":  (25,  80,  40),
        "neon":  (60,  255, 100),
        "eye":   (100, 255, 120),
        "metal": (45,  55,  45),
        "accent":(180, 255, 80),
        "hp_bonus": 0,
    },
    # 1 TITAN
    {
        "name": "TITAN",
        "title": "Titan Giáp Sắt",
        "head":  (160, 30,  30),
        "body":  (140, 25,  25),
        "limb":  (100, 20,  20),
        "neon":  (255, 60,  60),
        "eye":   (255, 120, 50),
        "metal": (50,  35,  35),
        "accent":(255, 160, 40),
        "hp_bonus": 50,
    },
    # 2 SPECTER
    {
        "name": "SPECTER",
        "title": "Bóng Ma Tím",
        "head":  (100, 40,  180),
        "body":  (80,  30,  160),
        "limb":  (60,  20,  130),
        "neon":  (200, 80,  255),
        "eye":   (220, 120, 255),
        "metal": (40,  30,  55),
        "accent":(255, 180, 255),
        "hp_bonus": -20,
    },
    # 3 WARDEN
    {
        "name": "WARDEN",
        "title": "Vệ Binh Vàng",
        "head":  (160, 130, 20),
        "body":  (140, 110, 15),
        "limb":  (110, 85,  10),
        "neon":  (255, 220, 50),
        "eye":   (255, 240, 100),
        "metal": (55,  50,  30),
        "accent":(255, 200, 0),
        "hp_bonus": 30,
    },
    # 4 PHANTOM
    {
        "name": "PHANTOM",
        "title": "Ảo Ảnh Băng",
        "head":  (20,  120, 180),
        "body":  (15,  100, 160),
        "limb":  (10,  80,  130),
        "neon":  (80,  220, 255),
        "eye":   (150, 240, 255),
        "metal": (25,  40,  55),
        "accent":(200, 255, 255),
        "hp_bonus": -10,
    },
    # 5 OVERLORD
    {
        "name": "OVERLORD",
        "title": "Hoàng Đế Cơ Khí",
        "head":  (180, 100, 20),
        "body":  (160, 80,  15),
        "limb":  (130, 65,  10),
        "neon":  (255, 180, 40),
        "eye":   (255, 150, 20),
        "metal": (55,  48,  30),
        "accent":(255, 220, 80),
        "hp_bonus": 80,
    },
    # 6 NEMESIS
    {
        "name": "NEMESIS",
        "title": "☠ NEMESIS BOSS",
        "head":  (140, 15,  15),
        "body":  (20,  20,  20),
        "limb":  (30,  30,  30),
        "neon":  (255, 20,  20),
        "eye":   (255, 0,   0),
        "metal": (20,  20,  25),
        "accent":(200, 0,   0),
        "hp_bonus": 120,
    },
    # 7 VIPER
    {
        "name": "VIPER",
        "title": "Rắn Điện Tử",
        "head":  (20,  120, 50),
        "body":  (15,  100, 40),
        "limb":  (10,  75,  30),
        "neon":  (40,  255, 100),
        "eye":   (180, 255, 80),
        "metal": (25,  45,  30),
        "accent":(200, 255, 60),
        "hp_bonus": -30,
    },
    # 8 COLOSSUS 
    {
        "name": "COLOSSUS",
        "title": "Khổng Lồ Thiên Thạch",
        "head":  (90,  65,  45),
        "body":  (75,  55,  35),
        "limb":  (60,  42,  28),
        "neon":  (255, 120, 30),
        "eye":   (255, 200, 80),
        "metal": (50,  42,  32),
        "accent":(255, 80,  20),
        "hp_bonus": 150,
    },
    # 9 ABYSS 
    {
        "name": "ABYSS",
        "title": "Vực Thẳm Vũ Trụ",
        "head":  (35,  15,  75),
        "body":  (28,  10,  60),
        "limb":  (20,  8,   48),
        "neon":  (180, 100, 255),
        "eye":   (220, 180, 255),
        "metal": (30,  20,  55),
        "accent":(255, 220, 255),
        "hp_bonus": 80,
    },
]


#   BASE ROBOT

class RobotRenderer:
    """
    Robot renderer đa hình: 7 kiểu robot với cùng hitbox API.
    robot_index (0-6) quyết định kiểu vẽ.
    """

    def __init__(self, center_x: int, center_y: int,
                 scale: float = 1.0, robot_index: int = 0):
        self.cx          = center_x
        self.cy          = center_y
        self.scale       = scale
        self.robot_index = robot_index % 10

        self._time        = 0.0
        self._hit_flash   = 0.0
        self._hit_zone    = None
        self._hit_shake_x = 0.0
        self._hit_shake_y = 0.0
        self._death_t     = 0.0
        self.is_dead      = False
        self._death_flash = False   # True khi mới chết → screen flash

        # Spawn animation (trượt vào từ phải)
        self._spawn_t     = 0.0   # 0→1 khi spawn
        self._spawn_offset = SCREEN_W // 2   # offset x khi spawn

        self._sparks  = []
        self._debris  = []
        self._glows   = []

        self.hitboxes = {}
        self._pal     = ROBOT_PALETTES[self.robot_index]

    @property
    def palette(self):
        return self._pal

    #  Public API 

    def update(self, dt: float):
        self._time += dt

        # Spawn slide-in
        if self._spawn_t < 1.0:
            self._spawn_t = min(1.0, self._spawn_t + dt * 2.5)

        self._hit_flash   = max(0.0, self._hit_flash - dt * 6)
        self._hit_shake_x *= 0.78
        self._hit_shake_y *= 0.78

        if self.is_dead:
            self._death_t = min(1.0, self._death_t + dt * 1.6)

        self._update_particles(dt)
        self._update_hitboxes()

    def trigger_hit(self, zone: str):
        self._hit_flash   = 1.0
        self._hit_zone    = zone
        self._hit_shake_x = random.uniform(-10, 10)
        self._hit_shake_y = random.uniform(-5,  5)
        self._spawn_impact(zone)

    def trigger_death(self):
        self.is_dead = True
        self._spawn_death_explosion()

    def check_hit(self, mx: int, my: int):
        for zone, rect in self.hitboxes.items():
            if rect.collidepoint(mx, my):
                return zone
        return None

    def draw(self, surface: pygame.Surface, show_hitboxes: bool = False):
        if self._death_t >= 1.0:
            self._draw_particles(surface)
            return

        # Spawn easing (ease-out cubic)
        t_ease   = 1 - (1 - self._spawn_t) ** 3
        spawn_off = int(self._spawn_offset * (1 - t_ease))

        alpha  = max(0.0, 1.0 - self._death_t * 1.6)
        bob    = math.sin(self._time * 1.6) * 5 * self.scale if not self.is_dead else 0
        death_drop = int(self._death_t * 420)

        cx = self.cx + int(self._hit_shake_x) + spawn_off
        cy = self.cy + int(bob) + death_drop

        # Vẽ robot theo index
        self._draw_shadow(surface, cx, cy)
        self._draw_ambient(surface, cx, cy, alpha)
        self._draw_energy_ground(surface, cx, cy, alpha)  # Ground energy ring

        idx = self.robot_index
        if   idx == 0: self._draw_grunt(surface, cx, cy, alpha)
        elif idx == 1: self._draw_titan(surface, cx, cy, alpha)
        elif idx == 2: self._draw_specter(surface, cx, cy, alpha)
        elif idx == 3: self._draw_warden(surface, cx, cy, alpha)
        elif idx == 4: self._draw_phantom(surface, cx, cy, alpha)
        elif idx == 5: self._draw_overlord(surface, cx, cy, alpha)
        elif idx == 6: self._draw_nemesis(surface, cx, cy, alpha)
        elif idx == 7: self._draw_viper(surface, cx, cy, alpha)
        elif idx == 8: self._draw_colossus(surface, cx, cy, alpha)
        elif idx == 9: self._draw_abyss(surface, cx, cy, alpha)

        self._draw_scan_lines_robot(surface, cx, cy, alpha)  # Holographic scanlines
        self._draw_particles(surface)

        if self._hit_flash > 0.02:
            self._draw_hit_vfx(surface, cx, cy, alpha)
            self._draw_chromatic_hit(surface, cx, cy)  # Chromatic aberration

        if show_hitboxes:
            for zone, rect in self.hitboxes.items():
                colors = {ZONE_HEAD_KEY:(255,80,80), ZONE_BODY_KEY:(80,180,255), ZONE_LIMB_KEY:(80,255,120)}
                pygame.draw.rect(surface, colors[zone], rect, 2)

    #  Hitboxes 

    def _update_hitboxes(self):
        G   = lambda v: int(v * self.scale)
        bob = math.sin(self._time * 1.6) * 5 * self.scale if not self.is_dead else 0
        cx  = self.cx
        cy  = self.cy + int(bob)

        # Điều chỉnh size hitbox theo từng robot 
        size_mods = [
            (1.0,  1.0),  # 0 GRUNT   
            (1.2,  1.2),  # 1 TITAN   
            (0.85, 0.85), # 2 SPECTER  
            (1.05, 1.05), # 3 WARDEN  
            (0.9,  0.9),  # 4 PHANTOM  
            (1.25, 1.25), # 5 OVERLORD 
            (1.3,  1.3),  # 6 NEMESIS  
            (0.8,  1.1),  # 7 VIPER    
            (1.4,  1.2),  # 8 COLOSSUS 
            (1.0,  1.05), # 9 ABYSS    
        ]
        ws, hs = size_mods[self.robot_index % len(size_mods)]

        self.hitboxes[ZONE_HEAD_KEY] = pygame.Rect(
            cx - G(int(46*ws)), cy - G(int(175*hs)), G(int(92*ws)), G(int(80*hs)))
        self.hitboxes[ZONE_BODY_KEY] = pygame.Rect(
            cx - G(int(58*ws)), cy - G(int(94*hs)),  G(int(116*ws)), G(int(98*hs)))
        self.hitboxes[ZONE_LIMB_KEY] = pygame.Rect(
            cx - G(int(108*ws)), cy - G(int(16*hs)), G(int(216*ws)), G(int(130*hs)))

    def _draw_energy_ground(self, surf, cx, cy, alpha):
        """Vòng năng lượng dưới chân robot — mỗi robot có màu riêng."""
        G  = lambda v: int(v * self.scale)
        nc = self._pal["neon"]
        t  = self._time
        for i in range(3):
            phase = t * 1.8 - i * 0.6
            r     = G(int(60 + i * 22 + 14 * math.sin(phase)))
            a     = int(alpha * (55 - i * 15) * (0.6 + 0.4 * math.sin(phase)))
            a     = max(0, min(255, a))
            if a < 4 or r < 2:
                continue
            gs = pygame.Surface((r * 2 + 4, max(1, r // 3)), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (nc[0], nc[1], nc[2], a), gs.get_rect())
            surf.blit(gs, (cx - r - 2, cy + G(126) - gs.get_height() // 2))

    def _draw_scan_lines_robot(self, surf, cx, cy, alpha):
        """Scanlines holographic trên thân robot."""
        if alpha < 0.3:
            return
        G   = lambda v: int(v * self.scale)
        t   = self._time
        nc  = self._pal["neon"]
        # Chỉ vẽ trong bounding box robot
        rx  = cx - G(80)
        ry  = cy - G(200)
        rw  = G(160)
        rh  = G(340)
        # Scan line chạy từ trên xuống
        scan_y = int((t * 80) % rh)
        a_scan = int(alpha * 40)
        if a_scan > 3:
            ss = pygame.Surface((rw, 4), pygame.SRCALPHA)
            ss.fill((nc[0], nc[1], nc[2], a_scan))
            surf.blit(ss, (rx, ry + scan_y))
        # Scanlines tĩnh mờ
        for yi in range(0, rh, 6):
            la = int(alpha * 10)
            if la > 2:
                sl = pygame.Surface((rw, 1), pygame.SRCALPHA)
                sl.fill((nc[0], nc[1], nc[2], la))
                surf.blit(sl, (rx, ry + yi))

    def _draw_chromatic_hit(self, surf, cx, cy):
        """Chromatic aberration khi bị bắn — RGB split."""
        G   = lambda v: int(v * self.scale)
        t   = self._hit_flash
        off = int(t * 8)
        if off < 1:
            return
        # Cắt vùng robot và shift RGB
        rw, rh = G(220), G(360)
        rx = cx - rw // 2
        ry = cy - G(220)
        if rx < 0 or ry < 0 or rx + rw > surf.get_width() or ry + rh > surf.get_height():
            return
        try:
            region = surf.subsurface(pygame.Rect(rx, ry, rw, rh)).copy()
            # Red channel shift right
            r_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
            r_surf.fill((0, 0, 0, 0))
            r_copy = region.copy()
            r_copy.fill((255, 0, 0, 60), special_flags=pygame.BLEND_MULT)
            surf.blit(r_copy, (rx + off, ry), special_flags=pygame.BLEND_ADD)
            # Blue channel shift left
            b_copy = region.copy()
            b_copy.fill((0, 0, 255, 60), special_flags=pygame.BLEND_MULT)
            surf.blit(b_copy, (rx - off, ry), special_flags=pygame.BLEND_ADD)
        except Exception:
            pass  # Bỏ qua nếu subsurface lỗi

    def _draw_shadow(self, surf, cx, cy):
        G  = lambda v: int(v * self.scale)
        sw = G(180)
        sh = G(30)
        s  = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for i in range(5):
            a = int(55 * (1 - i / 5))
            pygame.draw.ellipse(s, (0, 0, 0, a),
                pygame.Rect(i*8, i*3, sw-i*16, sh-i*6))
        surf.blit(s, (cx - sw//2, cy + G(125)))

    def _draw_ambient(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        p  = self._pal
        r  = G(90)
        gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        a  = int(22 * alpha * (0.7 + 0.3 * math.sin(self._time * 1.5)))
        pygame.draw.circle(gs, _rgba(p["neon"], a), (r, r), r)
        surf.blit(gs, (cx-r, cy - G(60)))

    def _draw_common_neon_glow(self, surf, cx, cy, alpha, head_r=None, body_r=None):
        """Viền neon xung quanh đầu và thân."""
        G = lambda v: int(v * self.scale)
        p = self._pal
        pulse = 0.55 + 0.45 * math.sin(self._time * 2.8)
        a = int(110 * alpha * pulse)
        if a < 8: return
        nc = p["neon"]
        hr = head_r or (G(100), G(88))
        br = body_r or (G(130), G(108))
        hy = cy - G(175)
        by = cy - G(94)
        # head glow
        gs = pygame.Surface((hr[0]+G(20), hr[1]+G(20)), pygame.SRCALPHA)
        pygame.draw.rect(gs, _rgba(nc, a), gs.get_rect(), width=3, border_radius=G(14))
        surf.blit(gs, (cx - hr[0]//2 - G(10), hy - G(10)))
        # body glow
        gs2 = pygame.Surface((br[0]+G(20), br[1]+G(20)), pygame.SRCALPHA)
        pygame.draw.rect(gs2, _rgba(nc, a), gs2.get_rect(), width=3, border_radius=G(12))
        surf.blit(gs2, (cx - br[0]//2 - G(10), by - G(10)))

    def _draw_eyes(self, surf, cx, ey, eye_gap, eye_or, eye_ir, alpha):
        """Mắt holographic chung."""
        G = lambda v: int(v * self.scale)
        p = self._pal
        for side in [-1, 1]:
            ex = cx + side * eye_gap
            # Socket
            pygame.draw.circle(surf, _ab((15,15,20), alpha), (ex, ey), eye_or)
            # Màu mắt pulse
            if self.is_dead:
                ec = (60, 20, 20)
            elif self._hit_flash > 0.3:
                ec = (255, 255, 255)
            else:
                ph = math.sin(self._time * 3.2 + side * 1.4)
                ec = (
                    max(0, min(255, int(p["eye"][0] * (0.7 + 0.3*ph)))),
                    max(0, min(255, int(p["eye"][1] * (0.8 + 0.2*ph)))),
                    max(0, min(255, int(p["eye"][2]))),
                )
            pygame.draw.circle(surf, _ab(ec, alpha), (ex, ey), eye_ir)
            # Bright core
            pygame.draw.circle(surf, _ab(_lt(ec, 1.8), alpha),
                               (ex - G(3), ey - G(3)), max(1, G(4)))
            # Glow
            if alpha > 0.4 and not self.is_dead:
                gw = eye_or * 3
                gs = pygame.Surface((gw*2, gw*2), pygame.SRCALPHA)
                ga = int(50 * alpha * (0.6 + 0.4*math.sin(self._time*2.2)))
                pygame.draw.circle(gs, _rgba(ec, ga), (gw, gw), gw)
                surf.blit(gs, (ex-gw, ey-gw))
            pygame.draw.circle(surf, _ab(_lt(p["neon"], 0.8), alpha), (ex, ey), eye_or, 1)

    #   ROBOT 0 — GRUNT

    def _draw_grunt(self, surf, cx, cy, alpha):
        G = lambda v: int(v * self.scale)
        p = self._pal

        # Chân thẳng cơ bản
        for sx in [-1, 1]:
            lx = cx + sx * G(28)
            # Ống chân
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (lx - G(12), cy + G(4), G(24), G(75)), border_radius=G(4))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.3), alpha),
                (lx - G(12), cy + G(4), G(24), G(75)), width=1, border_radius=G(4))
            # Bàn chân vuông
            pygame.draw.rect(surf, _ab(_dk(p["limb"],0.7), alpha),
                (lx - G(18), cy + G(78), G(36), G(14)), border_radius=G(3))

        # Tay
        for sx in [-1, 1]:
            ax = cx + sx * G(65)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (ax - G(12), cy - G(82), G(24), G(80)), border_radius=G(5))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.3), alpha),
                (ax - G(12), cy - G(82), G(24), G(80)), width=1, border_radius=G(5))
            # Khớp vai
            pygame.draw.circle(surf, _ab(p["metal"], alpha), (ax, cy - G(82)), G(10))
            pygame.draw.circle(surf, _ab(_lt(p["metal"],1.5), alpha), (ax, cy - G(82)), G(5))
            # Bàn tay
            pygame.draw.circle(surf, _ab(_dk(p["limb"],0.8), alpha),
                (ax, cy - G(2)), G(13))

        # Thân hộp
        bw, bh = G(110), G(92)
        bx, by = cx - bw//2, cy - G(92)
        pygame.draw.rect(surf, _ab(p["body"], alpha), (bx, by, bw, bh), border_radius=G(6))
        # Viền panel ngực
        pygame.draw.rect(surf, _ab(_lt(p["body"],1.4), alpha),
            (bx+G(8), by+G(10), G(42), G(34)), border_radius=G(4))
        pygame.draw.rect(surf, _ab(_lt(p["body"],1.4), alpha),
            (bx+bw-G(50), by+G(10), G(42), G(34)), border_radius=G(4))
        # Đường gân giữa thân
        for i in range(3):
            pygame.draw.line(surf, _ab(_lt(p["body"],0.7), alpha),
                (cx, by+G(8)+i*G(26)), (cx, by+G(8)+i*G(26)+G(18)), 2)
        # Viền thân
        pygame.draw.rect(surf, _ab(_lt(p["body"],1.4), alpha),
            (bx, by, bw, bh), width=2, border_radius=G(6))

        # Đầu hộp
        hw, hh = G(86), G(76)
        hx, hy = cx - hw//2, cy - G(170)
        pygame.draw.rect(surf, _ab(p["head"], alpha), (hx, hy, hw, hh), border_radius=G(8))
        pygame.draw.rect(surf, _ab(_lt(p["head"],1.4), alpha),
            (hx, hy, hw, hh), width=2, border_radius=G(8))
        # Ăng-ten đơn giữa
        pygame.draw.line(surf, _ab(_lt(p["head"],1.5), alpha),
            (cx, hy), (cx, hy-G(22)), 2)
        pygame.draw.circle(surf, _ab(p["accent"], alpha), (cx, hy-G(24)), G(5))
        # Mắt
        self._draw_eyes(surf, cx, hy+G(28), G(20), G(13), G(8), alpha)
        # Miệng đơn giản
        pygame.draw.rect(surf, _ab((10,10,10), alpha),
            (cx-G(20), hy+G(56), G(40), G(8)), border_radius=G(3))
        for i in range(4):
            pygame.draw.line(surf, _ab(p["neon"], alpha*0.5),
                (cx-G(16)+i*G(10), hy+G(58)), (cx-G(16)+i*G(10), hy+G(62)), 1)

        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(86), G(76)), body_r=(G(110), G(92)))

    #   ROBOT 1 — TITAN (to, bọc giáp dày)

    def _draw_titan(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        p  = self._pal

        # Chân ngắn to
        for sx in [-1, 1]:
            lx = cx + sx * G(36)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (lx - G(20), cy + G(5), G(40), G(65)), border_radius=G(6))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.3), alpha),
                (lx - G(20), cy + G(5), G(40), G(65)), width=2, border_radius=G(6))
            # Tấm giáp trước chân
            pygame.draw.rect(surf, _ab(_lt(p["limb"],0.8), alpha),
                (lx - G(16), cy + G(14), G(32), G(28)), border_radius=G(3))
            # Bàn chân to
            pygame.draw.rect(surf, _ab(_dk(p["limb"],0.7), alpha),
                (lx - G(26), cy + G(70), G(52), G(20)), border_radius=G(5))
            pygame.draw.rect(surf, _ab(p["accent"], alpha),
                (lx - G(26), cy + G(70), G(52), G(20)), width=1, border_radius=G(5))

        # Vai to (pauldrons)
        for sx in [-1, 1]:
            px = cx + sx * G(78)
            pygame.draw.ellipse(surf, _ab(p["limb"], alpha),
                (px - G(30), cy - G(95), G(50), G(44)))
            pygame.draw.ellipse(surf, _ab(_lt(p["limb"],1.4), alpha),
                (px - G(30), cy - G(95), G(50), G(44)), width=2)
            # Tấm giáp vai
            pygame.draw.rect(surf, _ab(_lt(p["limb"],0.9), alpha),
                (px - G(22), cy - G(88), G(34), G(20)), border_radius=G(4))

        # Tay to
        for sx in [-1, 1]:
            ax = cx + sx * G(76)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (ax - G(16), cy - G(76), G(32), G(72)), border_radius=G(6))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.3), alpha),
                (ax - G(16), cy - G(76), G(32), G(72)), width=2, border_radius=G(6))
            # Giáp cánh tay
            pygame.draw.rect(surf, _ab(_lt(p["limb"],0.8), alpha),
                (ax - G(12), cy - G(65), G(24), G(22)), border_radius=G(3))
            # Nắm đấm
            pygame.draw.rect(surf, _ab(_dk(p["limb"],0.85), alpha),
                (ax - G(18), cy - G(4), G(36), G(28)), border_radius=G(6))
            for i in range(4):
                pygame.draw.line(surf, _ab(_lt(p["limb"],0.5), alpha),
                    (ax - G(14)+i*G(9), cy+G(0)), (ax - G(14)+i*G(9), cy+G(22)), 2)

        # Thân rộng dày
        bw, bh = G(140), G(104)
        bx, by = cx - bw//2, cy - G(104)
        pygame.draw.rect(surf, _ab(p["body"], alpha), (bx, by, bw, bh), border_radius=G(8))
        # Giáp ngực trung tâm
        pygame.draw.rect(surf, _ab(_lt(p["body"],1.2), alpha),
            (cx - G(36), by+G(8), G(72), G(48)), border_radius=G(6))
        # Biểu tượng ngực
        pygame.draw.circle(surf, _ab(p["accent"], alpha), (cx, by+G(30)), G(14))
        pygame.draw.circle(surf, _ab(_lt(p["accent"],1.5), alpha), (cx, by+G(30)), G(8))
        pygame.draw.circle(surf, _ab(_lt(p["accent"],2.0), alpha), (cx, by+G(30)), G(3))
        # Viền thân
        pygame.draw.rect(surf, _ab(p["neon"], alpha*0.9),
            (bx, by, bw, bh), width=2, border_radius=G(8))

        # Đầu to hình vuông nghiêng
        hw, hh = G(100), G(84)
        hx, hy = cx - hw//2, cy - G(190)
        pygame.draw.rect(surf, _ab(p["head"], alpha), (hx, hy, hw, hh), border_radius=G(6))
        # Visor ngang
        visor_y = hy + G(22)
        visor_h = G(24)
        pygame.draw.rect(surf, _ab((5,5,8), alpha),
            (hx+G(6), visor_y, hw-G(12), visor_h), border_radius=G(4))
        # Mắt đơn (visor bar style)
        visor_pulse = int(200 + 55*math.sin(self._time*2.5))
        ec = (max(0,min(255,p["eye"][0])), visor_pulse if p["eye"][1]>100 else p["eye"][1], p["eye"][2])
        for i in range(5):
            a_eye = int(alpha * (180 - i*30))
            lx_v = hx + G(10) + i * (hw - G(20)) // 4
            pygame.draw.line(surf, _rgba(ec, max(0,a_eye)),
                (lx_v, visor_y+G(4)), (lx_v + (hw-G(20))//4 - G(4), visor_y+G(4)), G(4))
        # Ăng-ten kép
        for dx in [-G(28), G(28)]:
            pygame.draw.line(surf, _ab(_lt(p["head"],1.5), alpha),
                (cx+dx, hy), (cx+dx+dx//4, hy-G(26)), 3)
            pygame.draw.rect(surf, _ab(p["accent"], alpha),
                (cx+dx+dx//4-G(5), hy-G(32), G(10), G(8)), border_radius=G(2))
        pygame.draw.rect(surf, _ab(_lt(p["head"],1.5), alpha),
            (hx, hy, hw, hh), width=2, border_radius=G(6))

        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(100), G(84)), body_r=(G(140), G(104)))

    def _draw_specter(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        p  = self._pal
        t  = self._time

        # Hiệu ứng teleport flicker
        flicker = 0.85 + 0.15*math.sin(t*8.3)
        a_eff   = alpha * flicker

        # Chân mỏng uốn cong
        for sx in [-1, 1]:
            lx  = cx + sx * G(22)
            pts = [
                (lx,        cy + G(4)),
                (lx+sx*G(8),cy + G(30)),
                (lx+sx*G(4),cy + G(60)),
                (lx+sx*G(12),cy+ G(80)),
            ]
            pygame.draw.lines(surf, _ab(p["limb"], a_eff), False, pts, G(10))
            # Bàn chân nhọn
            pygame.draw.polygon(surf, _ab(_lt(p["limb"],1.3), a_eff), [
                (lx+sx*G(10), cy+G(78)),
                (lx+sx*G(18), cy+G(92)),
                (lx+sx*G(-4), cy+G(88)),
            ])

        # Tay dài mỏng cong
        for sx in [-1, 1]:
            ax, ay = cx + sx*G(52), cy - G(72)
            pts = [(ax, ay), (ax+sx*G(22), ay+G(28)),
                   (ax+sx*G(16), ay+G(60)), (ax+sx*G(28), ay+G(80))]
            pygame.draw.lines(surf, _ab(p["limb"], a_eff), False, pts, G(8))
            # Ngón tay cong như vuốt
            tip = pts[-1]
            for i in range(3):
                ang = math.radians(200 + i*25 + sx*30)
                tex = tip[0] + math.cos(ang)*G(16)
                tey = tip[1] + math.sin(ang)*G(16)
                pygame.draw.line(surf, _ab(_lt(p["limb"],1.4), a_eff),
                    tip, (int(tex), int(tey)), 2)

        # Thân mảnh hình thoi
        bpts = [
            (cx,            cy - G(98)),
            (cx + G(52),    cy - G(58)),
            (cx,            cy - G(2)),
            (cx - G(52),    cy - G(58)),
        ]
        pygame.draw.polygon(surf, _ab(p["body"], a_eff), bpts)
        pygame.draw.polygon(surf, _ab(_lt(p["body"],1.5), a_eff), bpts, 2)
        # Lõi năng lượng giữa thân
        core_pulse = 0.6 + 0.4*math.sin(t*4)
        core_r = G(int(16*core_pulse))
        pygame.draw.circle(surf, _ab(p["neon"], a_eff),
            (cx, cy - G(50)), core_r)
        pygame.draw.circle(surf, _ab(_lt(p["neon"],1.8), a_eff),
            (cx, cy - G(50)), max(1, core_r//2))
        # Particle orbit
        for i in range(4):
            ang = t*2 + i*math.pi/2
            ox  = cx + int(math.cos(ang)*G(28))
            oy  = cy - G(50) + int(math.sin(ang)*G(28))
            pygame.draw.circle(surf, _ab(p["accent"], a_eff*0.8), (ox, oy), G(3))
        # Viền thân neon
        gs = pygame.Surface((G(130), G(110)), pygame.SRCALPHA)
        pulse_a = int(100 * a_eff * (0.5+0.5*math.sin(t*3)))
        pygame.draw.polygon(gs, _rgba(p["neon"], pulse_a), [
            (G(65), G(5)), (G(120), G(45)), (G(65), G(105)), (G(10), G(45))
        ], 2)
        surf.blit(gs, (cx - G(65), cy - G(100)))

        # Đầu hình tam giác ngược
        hp = [
            (cx,         cy - G(172)),
            (cx + G(50), cy - G(140)),
            (cx + G(35), cy - G(108)),
            (cx - G(35), cy - G(108)),
            (cx - G(50), cy - G(140)),
        ]
        pygame.draw.polygon(surf, _ab(p["head"], a_eff), hp)
        pygame.draw.polygon(surf, _ab(_lt(p["head"],1.5), a_eff), hp, 2)
        # Mắt dạng scan-line hẹp
        eye_y = cy - G(132)
        for i, sx in enumerate([-1, 1]):
            ex = cx + sx * G(18)
            # Visor scan
            for li in range(3):
                la = int(a_eff * (180 - li*50))
                pygame.draw.line(surf, _rgba(p["eye"], max(0,la)),
                    (ex - G(14), eye_y - G(2)+li*G(5)),
                    (ex + G(14), eye_y - G(2)+li*G(5)), max(1, G(3)-li))
        # Glow đầu
        for ri in [G(30), G(50), G(70)]:
            gs2 = pygame.Surface((ri*2, ri*2), pygame.SRCALPHA)
            ga  = int(a_eff * (50 - ri//G(2)))
            if ga > 3:
                pygame.draw.circle(gs2, _rgba(p["neon"], ga), (ri, ri), ri, max(1, ri//8))
                surf.blit(gs2, (cx-ri, cy-G(140)-ri))

    #   ROBOT 3 — WARDEN (có khiên, vàng-nâu)

    def _draw_warden(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        p  = self._pal

        # Chân vừa
        for sx in [-1, 1]:
            lx = cx + sx * G(30)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (lx - G(14), cy+G(4), G(28), G(68)), border_radius=G(5))
            # Đệm gối
            pygame.draw.ellipse(surf, _ab(_lt(p["limb"],1.3), alpha),
                (lx - G(16), cy+G(42), G(32), G(18)))
            # Bàn chân
            pygame.draw.rect(surf, _ab(_dk(p["limb"],0.75), alpha),
                (lx - G(22), cy+G(72), G(44), G(16)), border_radius=G(5))

        # Tay phải cầm súng, tay trái có khiên
        for sx in [-1, 1]:
            ax = cx + sx * G(68)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (ax - G(13), cy-G(80), G(26), G(76)), border_radius=G(5))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.3), alpha),
                (ax - G(13), cy-G(80), G(26), G(76)), width=1, border_radius=G(5))
            # Khớp vai
            pygame.draw.circle(surf, _ab(p["metal"], alpha), (ax, cy-G(80)), G(12))
            pygame.draw.circle(surf, _ab(p["accent"], alpha), (ax, cy-G(80)), G(6))
        # KHIÊN tay trái
        shield_cx = cx - G(96)
        shield_pts = [
            (shield_cx - G(28), cy - G(78)),
            (shield_cx + G(28), cy - G(78)),
            (shield_cx + G(30), cy - G(14)),
            (shield_cx,         cy + G(24)),
            (shield_cx - G(30), cy - G(14)),
        ]
        pygame.draw.polygon(surf, _ab(p["body"], alpha), shield_pts)
        # Chi tiết khiên
        inner = [(int(x + (shield_cx - x)*0.2), int(y + (cy-G(28) - y)*0.2))
                 for x, y in shield_pts]
        pygame.draw.polygon(surf, _ab(_lt(p["body"],1.4), alpha), inner, 2)
        pygame.draw.circle(surf, _ab(p["accent"], alpha), (shield_cx, cy-G(28)), G(12))
        pygame.draw.circle(surf, _ab(_lt(p["accent"],1.6), alpha), (shield_cx, cy-G(28)), G(6))
        pygame.draw.polygon(surf, _ab(p["neon"], alpha*0.9), shield_pts, 2)

        # Thân
        bw, bh = G(118), G(96)
        bx, by = cx - bw//2, cy - G(96)
        pygame.draw.rect(surf, _ab(p["body"], alpha), (bx, by, bw, bh), border_radius=G(7))
        # Giáp ngực V-shape
        vpts = [(cx-G(38), by+G(8)), (cx, by+G(38)), (cx+G(38), by+G(8))]
        pygame.draw.lines(surf, _ab(p["accent"], alpha), False, vpts, G(4))
        # Huy hiệu
        pygame.draw.circle(surf, _ab(p["accent"], alpha), (cx, by+G(55)), G(14))
        pygame.draw.circle(surf, _ab((10,10,10), alpha), (cx, by+G(55)), G(10))
        pygame.draw.circle(surf, _ab(p["accent"], alpha), (cx, by+G(55)), G(5))
        pygame.draw.rect(surf, _ab(p["neon"], alpha), (bx, by, bw, bh), width=2, border_radius=G(7))

        # Đầu hình thang
        hw, hh = G(88), G(78)
        hx, hy = cx - hw//2, cy - G(176)
        # Hình thang (rộng dưới, hẹp trên)
        head_pts = [
            (cx - G(30), hy),
            (cx + G(30), hy),
            (cx + G(44), hy + hh),
            (cx - G(44), hy + hh),
        ]
        pygame.draw.polygon(surf, _ab(p["head"], alpha), head_pts)
        pygame.draw.polygon(surf, _ab(_lt(p["head"],1.4), alpha), head_pts, 2)
        # Mũ giáp trên đầu
        crest_pts = [
            (cx-G(30), hy), (cx, hy-G(20)), (cx+G(30), hy)
        ]
        pygame.draw.polygon(surf, _ab(_lt(p["head"],1.2), alpha), crest_pts)
        pygame.draw.polygon(surf, _ab(p["neon"], alpha), crest_pts, 2)
        # Mắt
        self._draw_eyes(surf, cx, hy+G(32), G(22), G(12), G(8), alpha)
        # Miệng có lưới
        pygame.draw.rect(surf, _ab((8,8,8), alpha),
            (cx-G(22), hy+G(56), G(44), G(14)), border_radius=G(5))
        for i in range(5):
            pygame.draw.line(surf, _ab(p["neon"], alpha*0.4),
                (cx-G(18)+i*G(9), hy+G(58)), (cx-G(18)+i*G(9), hy+G(68)), 1)
        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(90), G(78)), body_r=(G(118), G(96)))


    #   ROBOT 4 — PHANTOM (băng, mảnh, cong)
 
    def _draw_phantom(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        p  = self._pal
        t  = self._time

        # Ice crystal effect: hào quang băng
        for ri in [G(50), G(80), G(115)]:
            gs = pygame.Surface((ri*2, ri*2), pygame.SRCALPHA)
            a  = int(alpha * 20 * (0.5 + 0.5*math.sin(t*1.8 + ri*0.02)))
            pygame.draw.circle(gs, _rgba(p["neon"], a), (ri, ri), ri, max(1, ri//10))
            surf.blit(gs, (cx-ri, cy-G(70)-ri))

        # Chân cong nhẹ
        for sx in [-1, 1]:
            lx = cx + sx*G(24)
            for yi in range(5):
                t_y = yi/5
                lw  = int(G(20) * (1 - t_y*0.4))
                ly  = cy + G(4) + int(G(72) * t_y)
                lxc = lx + sx*int(G(10)*math.sin(t_y*math.pi))
                pygame.draw.rect(surf, _ab(p["limb"], alpha*(1-t_y*0.3)),
                    (lxc - lw//2, ly, lw, G(16)), border_radius=G(4))
            # Tinh thể chân
            tip_x = lx + sx*G(10)
            pygame.draw.polygon(surf, _ab(_lt(p["limb"],1.5), alpha), [
                (tip_x,       cy+G(80)),
                (tip_x+sx*G(16), cy+G(95)),
                (tip_x-sx*G(8),  cy+G(95)),
            ])

        # Tay dài tinh tế
        for sx in [-1, 1]:
            ax = cx + sx*G(58)
            swing = math.sin(t*1.8+sx) * G(6)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (ax-G(10), cy-G(80)+int(swing), G(20), G(76)), border_radius=G(6))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.4), alpha),
                (ax-G(10), cy-G(80)+int(swing), G(20), G(76)), width=1, border_radius=G(6))
            # Tinh thể tay
            fy = cy - G(4) + int(swing)
            pygame.draw.polygon(surf, _ab(p["neon"], alpha*0.9), [
                (ax-G(8),  fy), (ax, fy-G(10)),
                (ax+G(8),  fy), (ax, fy+G(18)),
            ])

        # Thân elipse dọc
        bw, bh = G(100), G(104)
        bx, by = cx-bw//2, cy-G(100)
        pygame.draw.ellipse(surf, _ab(p["body"], alpha), (bx, by, bw, bh))
        # Chi tiết tinh thể
        for i in range(4):
            ang = t*0.8 + i*math.pi/2
            cr  = G(30)
            cpx = cx + int(math.cos(ang)*cr)
            cpy = cy - G(50) + int(math.sin(ang)*G(18))
            pygame.draw.line(surf, _ab(p["neon"], alpha*0.7),
                (cx, cy-G(50)), (cpx, cpy), 1)
        # Tinh thể ngực
        crystal_pts = [(cx, by+G(12)), (cx+G(20), by+G(40)),
                       (cx, by+G(70)), (cx-G(20), by+G(40))]
        pygame.draw.polygon(surf, _ab(_lt(p["body"],1.3), alpha), crystal_pts)
        pygame.draw.polygon(surf, _ab(p["neon"], alpha*0.8), crystal_pts, 2)
        pygame.draw.ellipse(surf, _ab(p["neon"], alpha*0.7),
            (bx, by, bw, bh), width=2)

        # Đầu elipse dọc
        hw, hh = G(78), G(92)
        hx, hy = cx-hw//2, cy-G(185)
        pygame.draw.ellipse(surf, _ab(p["head"], alpha), (hx, hy, hw, hh))
        pygame.draw.ellipse(surf, _ab(_lt(p["head"],1.5), alpha), (hx, hy, hw, hh), 2)
        # Vương miện băng
        for i in range(5):
            crown_x = hx + G(8) + i*G(14)
            h_crown = G(10) + (G(16) if i in [1,3] else 0)
            pygame.draw.polygon(surf, _ab(p["accent"], alpha*0.9), [
                (crown_x, hy), (crown_x+G(6), hy-h_crown), (crown_x+G(12), hy)
            ])
        # Mắt
        self._draw_eyes(surf, cx, hy+G(36), G(18), G(12), G(7), alpha)
        # Tinh thể miệng
        mouth_y = hy + G(68)
        for i in range(3):
            mw = G(6) + (G(4) if i==1 else 0)
            mx2 = cx - G(14) + i*G(14)
            pygame.draw.polygon(surf, _ab(p["neon"], alpha*0.8), [
                (mx2, mouth_y), (mx2+mw//2, mouth_y+G(12)), (mx2+mw, mouth_y)
            ])

        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(78), G(92)), body_r=(G(100), G(104)))
        
    #  ROBOT 5 — OVERLORD (chỉ huy, to, vàng hoàng gia)
    
    def _draw_overlord(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        p  = self._pal
        t  = self._time

        # Cape/áo choàng (vẽ trước)
        cape_pts = [
            (cx-G(70), cy-G(92)),
            (cx+G(70), cy-G(92)),
            (cx+G(90), cy+G(40)),
            (cx+G(50), cy+G(80)),
            (cx-G(50), cy+G(80)),
            (cx-G(90), cy+G(40)),
        ]
        pygame.draw.polygon(surf, _ab(_dk(p["body"],0.6), alpha*0.7), cape_pts)
        pygame.draw.polygon(surf, _ab(p["neon"], alpha*0.4), cape_pts, 2)

        # Chân to + áo dài che
        for sx in [-1, 1]:
            lx = cx + sx*G(34)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (lx-G(18), cy+G(3), G(36), G(70)), border_radius=G(6))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.3), alpha),
                (lx-G(18), cy+G(3), G(36), G(70)), width=2, border_radius=G(6))
            # Chỉ vàng trang trí
            for yi in range(3):
                pygame.draw.line(surf, _ab(p["accent"], alpha*0.6),
                    (lx-G(14), cy+G(15)+yi*G(18)), (lx+G(14), cy+G(15)+yi*G(18)), 1)
            pygame.draw.rect(surf, _ab(_dk(p["limb"],0.7), alpha),
                (lx-G(24), cy+G(73), G(48), G(18)), border_radius=G(5))

        # Tay to + vòng trang sức
        for sx in [-1, 1]:
            ax = cx + sx*G(74)
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (ax-G(16), cy-G(84), G(32), G(80)), border_radius=G(6))
            # Vòng vai trang sức
            for ri in [0, G(12), G(26)]:
                pygame.draw.rect(surf, _ab(p["accent"], alpha),
                    (ax-G(17), cy-G(84)+ri, G(34), G(8)), border_radius=G(2))
            pygame.draw.rect(surf, _ab(_lt(p["limb"],1.3), alpha),
                (ax-G(16), cy-G(84), G(32), G(80)), width=1, border_radius=G(6))
            # Bàn tay đeo nhẫn
            pygame.draw.rect(surf, _ab(_dk(p["limb"],0.85), alpha),
                (ax-G(20), cy-G(4), G(40), G(28)), border_radius=G(7))
            pygame.draw.circle(surf, _ab(p["accent"], alpha), (ax, cy+G(8)), G(8))

        # Thân hùng vĩ
        bw, bh = G(132), G(108)
        bx, by = cx-bw//2, cy-G(108)
        pygame.draw.rect(surf, _ab(p["body"], alpha), (bx, by, bw, bh), border_radius=G(8))
        # Giáp ngực hoàng tộc
        for i in range(3):
            w = bw - i*G(20)
            x = bx + i*G(10)
            pygame.draw.rect(surf, _ab(_lt(p["body"],1.1+i*0.1), alpha),
                (x, by+i*G(10), w, G(20)-i*G(2)), border_radius=G(4))
        # Huy chương
        pygame.draw.circle(surf, _ab(p["accent"], alpha), (cx, by+G(58)), G(22))
        pygame.draw.circle(surf, _ab(_dk(p["accent"],0.5), alpha), (cx, by+G(58)), G(16))
        pygame.draw.circle(surf, _ab(_lt(p["accent"],1.6), alpha), (cx, by+G(58)), G(8))
        # Tia hào quang huy chương
        for i in range(8):
            ang = i*math.pi/4 + t*0.5
            r1, r2 = G(22), G(34)
            x1 = cx + int(math.cos(ang)*r1)
            y1 = by + G(58) + int(math.sin(ang)*r1)
            x2 = cx + int(math.cos(ang)*r2)
            y2 = by + G(58) + int(math.sin(ang)*r2)
            pygame.draw.line(surf, _ab(p["neon"], alpha*0.7), (x1,y1), (x2,y2), 2)
        pygame.draw.rect(surf, _ab(p["neon"], alpha), (bx, by, bw, bh), width=2, border_radius=G(8))

        # Đầu với vương miện
        hw, hh = G(92), G(80)
        hx, hy = cx-hw//2, cy-G(190)
        pygame.draw.rect(surf, _ab(p["head"], alpha), (hx, hy, hw, hh), border_radius=G(8))
        # Vương miện
        crown_y = hy - G(4)
        for i in range(5):
            cx2 = hx + G(8) + i*G(18)
            h_pts = G(24) if i in [1,3] else G(16)
            pygame.draw.polygon(surf, _ab(p["accent"], alpha), [
                (cx2, crown_y), (cx2+G(7), crown_y-h_pts), (cx2+G(14), crown_y)
            ])
            # Đá quý
            if i in [1, 3]:
                pygame.draw.circle(surf, _ab(_lt(p["accent"],2.0), alpha),
                    (cx2+G(7), crown_y-h_pts+G(4)), G(4))
        # Mắt uy quyền
        self._draw_eyes(surf, cx, hy+G(30), G(24), G(14), G(9), alpha)
        # Râu/cằm trang trí
        pygame.draw.rect(surf, _ab(_dk(p["head"],0.7), alpha),
            (cx-G(16), hy+hh-G(12), G(32), G(14)), border_radius=G(6))
        for i in range(3):
            pygame.draw.line(surf, _ab(p["neon"], alpha*0.5),
                (cx-G(12)+i*G(12), hy+hh-G(10)), (cx-G(12)+i*G(12), hy+hh-G(2)), 1)
        pygame.draw.rect(surf, _ab(_lt(p["head"],1.5), alpha),
            (hx, hy, hw, hh), width=2, border_radius=G(8))

        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(92), G(80)), body_r=(G(132), G(108)))


    #   ROBOT 6 — NEMESIS (BOSS, cánh cơ học, ominous)

    def _draw_nemesis(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        p  = self._pal
        t  = self._time

        # Aura lửa địa ngục
        for ri in [G(60), G(100), G(145)]:
            a  = int(alpha * 30 * (0.4 + 0.6*abs(math.sin(t*2.2 + ri*0.01))))
            gs = pygame.Surface((ri*2, ri*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, _rgba(p["neon"], a), (ri, ri), ri, max(2, ri//8))
            surf.blit(gs, (cx-ri, cy-G(80)-ri))

        # Cánh cơ học (vẽ trước thân)
        wing_angle = math.sin(t*1.4) * 0.12
        for sx in [-1, 1]:
            # Cánh gồm 3 segment
            base_x = cx + sx*G(60)
            base_y = cy - G(88)
            for si in range(3):
                angle = math.radians(-90 + sx*(30 + si*25) + sx*math.degrees(wing_angle)*si)
                length = G(int(80 - si*18))
                tip_x  = int(base_x + math.cos(angle)*length)
                tip_y  = int(base_y + math.sin(angle)*length)
                thickness = max(2, G(16) - si*G(4))
                pygame.draw.line(surf, _ab(p["metal"], alpha*0.9),
                    (base_x, base_y), (tip_x, tip_y), thickness+2)
                pygame.draw.line(surf, _ab(p["neon"], alpha*0.7),
                    (base_x, base_y), (tip_x, tip_y), max(1, thickness//3))
                # Gai cánh
                for gi in range(2):
                    gp  = 0.4 + gi*0.3
                    gx  = int(base_x + math.cos(angle)*length*gp)
                    gy2 = int(base_y + math.sin(angle)*length*gp)
                    spike_ang = angle + sx*math.pi/2.5
                    pygame.draw.line(surf, _ab(_lt(p["limb"],1.2), alpha),
                        (gx, gy2),
                        (int(gx+math.cos(spike_ang)*G(18)),
                         int(gy2+math.sin(spike_ang)*G(18))), 2)
                base_x, base_y = tip_x, tip_y

        # Chân robot địa ngục
        for sx in [-1, 1]:
            lx = cx + sx*G(32)
            # Ống chân đen
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (lx-G(16), cy+G(4), G(32), G(72)), border_radius=G(5))
            # Gai bên chân
            for gi in range(3):
                gy2 = cy + G(20) + gi*G(18)
                spike_x = lx + sx*(G(16)+G(8))
                pygame.draw.polygon(surf, _ab(p["neon"], alpha*0.8), [
                    (lx+sx*G(16), gy2),
                    (spike_x, gy2-G(5)),
                    (spike_x, gy2+G(5)),
                ])
            pygame.draw.rect(surf, _ab(p["neon"], alpha*0.5),
                (lx-G(16), cy+G(4), G(32), G(72)), width=1, border_radius=G(5))
            # Móng chân nhọn
            for mi in range(3):
                mangle = math.radians(200 + mi*20 + sx*40)
                mx2 = lx + int(math.cos(mangle)*G(24))
                my2 = cy + G(76) + int(math.sin(mangle)*G(24))
                pygame.draw.line(surf, _ab(p["neon"], alpha),
                    (lx, cy+G(72)), (mx2, my2), 2)

        # Tay cơ học khổng lồ
        for sx in [-1, 1]:
            ax = cx + sx*G(78)
            # Cánh tay 2 đốt
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (ax-G(18), cy-G(82), G(36), G(40)), border_radius=G(5))
            # Khớp khuỷu đặc biệt
            elbow_y = cy - G(42)
            pygame.draw.circle(surf, _ab(p["metal"], alpha), (ax, elbow_y), G(14))
            pygame.draw.circle(surf, _ab(p["neon"], alpha*0.8), (ax, elbow_y), G(8))
            pygame.draw.circle(surf, _ab(_lt(p["neon"],2.0), alpha), (ax, elbow_y), G(3))
            # Cánh tay dưới
            pygame.draw.rect(surf, _ab(p["limb"], alpha),
                (ax-G(15), elbow_y, G(30), G(48)), border_radius=G(5))
            pygame.draw.rect(surf, _ab(p["neon"], alpha*0.5),
                (ax-G(18), cy-G(82), G(36), G(88)+G(14)), width=1, border_radius=G(5))
            # Móng tay (claw)
            for ci in range(4):
                ca = math.radians(220 + ci*20 + sx*(-10))
                cx3 = ax + int(math.cos(ca)*G(30))
                cy3 = elbow_y + G(48) + int(math.sin(ca)*G(24))
                pygame.draw.line(surf, _ab(p["neon"], alpha),
                    (ax, elbow_y+G(48)), (cx3, cy3), G(3))

        # Thân giáp đen tuyền
        bw, bh = G(128), G(110)
        bx, by = cx-bw//2, cy-G(110)
        pygame.draw.rect(surf, _ab(p["body"], alpha), (bx, by, bw, bh), border_radius=G(6))
        # Lõi năng lượng đỏ
        pulse = 0.5 + 0.5*abs(math.sin(t*3))
        core_r = G(int(20*pulse))
        for ri, a_mult in [(G(40), 0.2), (G(28), 0.4), (core_r, 1.0)]:
            gs = pygame.Surface((ri*2, ri*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, _rgba(p["neon"], int(alpha*a_mult*200)), (ri, ri), ri)
            surf.blit(gs, (cx-ri, cy-G(55)-ri))
        # Xương sườn cơ học
        for i in range(4):
            rib_y = by + G(20) + i*G(18)
            pygame.draw.line(surf, _ab(_lt(p["body"],2.5), alpha*0.5),
                (bx+G(4), rib_y), (cx-G(18), rib_y), 1)
            pygame.draw.line(surf, _ab(_lt(p["body"],2.5), alpha*0.5),
                (cx+G(18), rib_y), (bx+bw-G(4), rib_y), 1)
        pygame.draw.rect(surf, _ab(p["neon"], alpha*0.9),
            (bx, by, bw, bh), width=3, border_radius=G(6))
        # Viền nguy hiểm
        for i in range(0, bw, G(20)):
            c_warn = p["neon"] if (i // G(20)) % 2 == 0 else _dk(p["neon"],0.3)
            pygame.draw.line(surf, _ab(c_warn, alpha*0.4),
                (bx+i, by+bh-G(4)), (bx+i+G(16), by+bh-G(4)), 2)

        # Đầu ominous (hình thang ngược nhọn)
        hw, hh = G(92), G(84)
        hx, hy = cx-hw//2, cy-G(196)
        head_pts = [
            (cx-G(46), hy+hh),
            (cx-G(28), hy),
            (cx+G(28), hy),
            (cx+G(46), hy+hh),
        ]
        pygame.draw.polygon(surf, _ab(p["head"], alpha), head_pts)
        # Sừng
        for sx in [-1, 1]:
            horn_base_x = cx + sx*G(22)
            horn_base_y = hy
            pygame.draw.polygon(surf, _ab(_lt(p["head"],1.4), alpha), [
                (horn_base_x-G(4), horn_base_y),
                (horn_base_x+sx*G(8), horn_base_y-G(32)),
                (horn_base_x+G(4), horn_base_y),
            ])
            pygame.draw.polygon(surf, _ab(p["neon"], alpha*0.9), [
                (horn_base_x-G(4), horn_base_y),
                (horn_base_x+sx*G(8), horn_base_y-G(32)),
                (horn_base_x+G(4), horn_base_y),
            ], 1)
        # Mắt NEMESIS - scan ominous
        eye_y = hy + G(34)
        for sx in [-1, 1]:
            ex = cx + sx*G(20)
            # Scan bar animation
            scan_offset = int(G(10) * math.sin(t*4 + sx))
            for li in range(4):
                la = int(alpha * (200 - li*45))
                pygame.draw.line(surf, _rgba(p["eye"], max(0, la)),
                    (ex-G(18), eye_y - G(10) + li*G(6) + scan_offset),
                    (ex+G(18), eye_y - G(10) + li*G(6) + scan_offset), G(3)-li//2)
        # Gương mặt ký tự nguy hiểm
        pygame.draw.polygon(surf, _ab(p["head"], alpha*0.5), head_pts, 2)
        pygame.draw.polygon(surf, _ab(p["neon"], alpha), head_pts, 2)

        # "BOSS" label
        boss_surf = pygame.Surface((G(80), G(18)), pygame.SRCALPHA)
        pygame.draw.rect(boss_surf, _rgba(p["neon"], int(alpha*160)),
            boss_surf.get_rect(), border_radius=G(3))
        surf.blit(boss_surf, (cx-G(40), hy-G(22)))

        # Glow đầu dữ dội
        for ri in [G(50), G(80)]:
            gs = pygame.Surface((ri*2, ri*2), pygame.SRCALPHA)
            a2 = int(alpha * 40 * abs(math.sin(t*3)))
            pygame.draw.circle(gs, _rgba(p["neon"], a2), (ri, ri), ri, max(2, ri//6))
            surf.blit(gs, (cx-ri, hy+hh//2-ri))

        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(100), G(90)), body_r=(G(140), G(116)))

    #   PARTICLES

    def _spawn_impact(self, zone: str):
        zone_colors = {
            ZONE_HEAD_KEY: self._pal["head"],
            ZONE_BODY_KEY: self._pal["body"],
            ZONE_LIMB_KEY: self._pal["limb"],
        }
        color = zone_colors.get(zone, (255, 200, 50))
        neon  = self._pal["neon"]
        rect  = self.hitboxes.get(zone)
        if not rect: return
        ox, oy = rect.centerx, rect.centery

        for _ in range(22):
            ang = random.uniform(0, math.pi*2)
            spd = random.uniform(2.5, 8)
            c   = neon if random.random() < 0.4 else color
            self._sparks.append({
                "x": float(ox), "y": float(oy),
                "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd - random.uniform(1,5),
                "life": random.uniform(0.5, 1.4),
                "size": random.uniform(2, 6),
                "color": c, "trail": [],
            })
        G = lambda v: int(v * self.scale)
        for _ in range(10):
            ang = random.uniform(0, math.pi*2)
            spd = random.uniform(1, 3.5)
            self._debris.append({
                "x": float(ox+random.randint(-20,20)), "y": float(oy+random.randint(-10,10)),
                "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd - 1.5,
                "life": random.uniform(0.6, 1.1),
                "w": random.randint(G(4), G(14)), "h": random.randint(G(2), G(7)),
                "rot": random.uniform(0,360), "rot_spd": random.uniform(-240,240),
                "color": (65, 70, 90),
            })
        self._glows.append({
            "x": float(ox), "y": float(oy),
            "r": 0.0, "max_r": 65.0*self.scale,
            "life": 1.0, "color": neon,
        })

    def _spawn_death_explosion(self):
        nc = self._pal["neon"]
        # 1) Big spark burst
        for _ in range(80):
            ang = random.uniform(0, math.pi*2)
            spd = random.uniform(3, 14)
            c   = random.choice([nc, self._pal["accent"],
                                  self._pal["head"], (255,200,50), (255,255,200)])
            self._sparks.append({
                "x": float(self.cx), "y": float(self.cy - 50*self.scale),
                "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd - random.uniform(2,8),
                "life": random.uniform(1.2, 3.2),
                "size": random.uniform(3, 12), "color": c, "trail": [],
            })

        # 2) Dismemberment parts: đầu, thân, tay trái, tay phải, chân trái, chân phải
        G = self.scale
        parts = [
            {"w":int(40*G), "h":int(35*G), "ox":0,       "oy":-130*G, "color":self._pal["head"],  "vx":random.uniform(-3,3),  "vy":random.uniform(-9,-5)},
            {"w":int(50*G), "h":int(60*G), "ox":0,       "oy":-70*G,  "color":self._pal["body"],  "vx":random.uniform(-1,1),  "vy":random.uniform(-4,-1)},
            {"w":int(18*G), "h":int(50*G), "ox":-45*G,   "oy":-80*G,  "color":self._pal["limb"],  "vx":random.uniform(-6,-3), "vy":random.uniform(-8,-3)},
            {"w":int(18*G), "h":int(50*G), "ox": 45*G,   "oy":-80*G,  "color":self._pal["limb"],  "vx":random.uniform(3,6),   "vy":random.uniform(-8,-3)},
            {"w":int(16*G), "h":int(55*G), "ox":-22*G,   "oy":-10*G,  "color":self._pal["limb"],  "vx":random.uniform(-4,-1), "vy":random.uniform(-5,-1)},
            {"w":int(16*G), "h":int(55*G), "ox": 22*G,   "oy":-10*G,  "color":self._pal["limb"],  "vx":random.uniform(1,4),   "vy":random.uniform(-5,-1)},
        ]
        for p in parts:
            self._debris.append({
                "x": float(self.cx + p["ox"]),
                "y": float(self.cy + p["oy"]),
                "vx": p["vx"], "vy": p["vy"],
                "life": random.uniform(1.4, 2.6),
                "w": max(1, p["w"]), "h": max(1, p["h"]),
                "rot": random.uniform(0,360),
                "rot_spd": random.uniform(-360, 360),
                "color": p["color"],
            })

        # 3) Small metal debris
        for _ in range(20):
            ang = random.uniform(0, math.pi*2)
            spd = random.uniform(1, 4)
            self._debris.append({
                "x": float(self.cx+random.randint(-30,30)),
                "y": float(self.cy - random.randint(30,120)),
                "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd - 2,
                "life": random.uniform(0.8, 1.8),
                "w": random.randint(4,12), "h": random.randint(2,6),
                "rot": random.uniform(0,360), "rot_spd": random.uniform(-400,400),
                "color": (65,70,90),
            })

        # 4) Glow explosions
        for _ in range(8):
            self._glows.append({
                "x": float(self.cx+random.randint(-60,60)),
                "y": float(self.cy - random.randint(0,150)*G),
                "r": 0.0, "max_r": random.uniform(100, 200)*G,
                "life": 1.0, "color": random.choice([nc, self._pal["accent"]]),
            })

        # 5) Screen flash marker (đọc từ gameplay để trigger slow-mo)
        self._death_flash = True

    def _update_particles(self, dt):
        for sp in self._sparks[:]:
            sp["trail"].append((sp["x"], sp["y"]))
            if len(sp["trail"]) > 6: sp["trail"].pop(0)
            sp["life"] -= dt*1.5
            sp["x"] += sp["vx"]*dt*60; sp["y"] += sp["vy"]*dt*60
            sp["vy"] += 0.28; sp["vx"] *= 0.97
            if sp["life"] <= 0: self._sparks.remove(sp)
        for db in self._debris[:]:
            db["life"] -= dt*1.5
            db["x"] += db["vx"]*dt*60; db["y"] += db["vy"]*dt*60
            db["vy"] += 0.22; db["rot"] += db["rot_spd"]*dt
            if db["life"] <= 0: self._debris.remove(db)
        for gl in self._glows[:]:
            gl["life"] -= dt*2.8
            gl["r"] += (gl["max_r"] - gl["r"])*dt*9
            if gl["life"] <= 0: self._glows.remove(gl)

    def _draw_particles(self, surf):
        def clamp(v): return max(0, min(255, int(v)))
        def rgba(c, a): return (clamp(c[0]), clamp(c[1]), clamp(c[2]), clamp(a))

        for gl in self._glows:
            a = clamp(gl["life"] * 170)
            r = int(gl["r"])
            if r < 2 or a < 5:
                continue
            gs = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, rgba(gl["color"], a),
                               (r + 2, r + 2), r, max(1, int(r * 0.14)))
            surf.blit(gs, (int(gl["x"]) - r - 2, int(gl["y"]) - r - 2))

        for db in self._debris:
            a = clamp(db["life"] * 255)
            if a < 5:
                continue
            w = max(1, int(db["w"]))
            h = max(1, int(db["h"]))
            ds = pygame.Surface((w, h), pygame.SRCALPHA)
            ds.fill(rgba(db["color"], a))
            rot = pygame.transform.rotate(ds, db["rot"] % 360)
            surf.blit(rot, (int(db["x"]) - rot.get_width() // 2,
                            int(db["y"]) - rot.get_height() // 2))

        for sp in self._sparks:
            a    = clamp(sp["life"] * 255)
            size = max(1, int(sp["size"] * sp["life"]))
            if a < 5:
                continue
            if len(sp["trail"]) >= 2:
                for ti in range(len(sp["trail"]) - 1):
                    ta = clamp(a * (ti + 1) / len(sp["trail"]) * 0.5)
                    if ta > 5:
                        pygame.draw.line(surf,
                            rgba(sp["color"], ta),
                            (int(sp["trail"][ti][0]),     int(sp["trail"][ti][1])),
                            (int(sp["trail"][ti + 1][0]), int(sp["trail"][ti + 1][1])),
                            1)
            ss = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(ss, rgba(sp["color"], a), (size, size), size)
            if size > 2:
                pygame.draw.circle(ss, rgba((255, 255, 255), a),
                                   (size, size), max(1, size // 2))
            surf.blit(ss, (int(sp["x"]) - size, int(sp["y"]) - size))

    def _draw_hit_vfx(self, surf, cx, cy, alpha):
        G  = lambda v: int(v * self.scale)
        t  = self._hit_flash
        nc = self._pal["neon"]
        fw, fh = G(280), G(340)
        fs = pygame.Surface((fw, fh), pygame.SRCALPHA)
        fs.fill((nc[0], nc[1], nc[2], int(t*80)))
        surf.blit(fs, (cx-fw//2, cy-G(230)))
        for ro in range(4):
            a = int(t*(70 - ro*18))
            if a > 5:
                pygame.draw.rect(surf, _rgba(nc, a),
                    (cx-G(66)-ro*3, cy-G(112)-ro*3,
                     G(132)+ro*6, G(112)+ro*6), width=2, border_radius=G(10))

    #   ROBOT 7 — VIPER  (Rắn Cơ Giới)
    #   Thân phân đốt, khớp servo, đuôi lò xo thủy lực
   
    def _draw_viper(self, surf, cx, cy, alpha):
        G = lambda v: int(v * self.scale)
        p = self._pal
        t = self._time

        # ── Đuôi phân đốt cơ khí ──────────────────────────────
        for i in range(7):
            wx = cx + int(math.sin(t*2.5 + i*0.6) * G(14))
            sy = cy + G(60) + i * G(16)
            sw = max(2, G(18 - i*2)); sh = G(10)
            pygame.draw.rect(surf, _ab(p["body"], alpha*0.9),
                (wx-sw//2, sy, sw, sh), border_radius=G(3))
            pygame.draw.rect(surf, _ab(p["neon"], alpha*0.5),
                (wx-sw//2, sy, sw, sh), width=1, border_radius=G(3))
            # Khớp servo
            pygame.draw.circle(surf, _ab(p["metal"], alpha), (wx, sy+sh//2), max(2,G(4-i//2)))
            pygame.draw.circle(surf, _ab(p["neon"], alpha*0.7), (wx, sy+sh//2), max(1,G(2)))

        # ── Chân 2 khớp cơ khí ────────────────────────────────
        for sx in [-1, 1]:
            sway = math.sin(t*3.5 + sx*1.2) * G(6)
            hip_x = cx + sx*G(20); hip_y = cy + G(8)
            pygame.draw.circle(surf, _ab(p["metal"], alpha), (hip_x, hip_y), G(9))
            pygame.draw.circle(surf, _ab(p["neon"], alpha*0.8), (hip_x, hip_y), G(5))
            knee_x = cx + sx*G(26) + int(sway); knee_y = cy + G(50)
            pygame.draw.line(surf, _ab(p["limb"], alpha), (hip_x,hip_y), (knee_x,knee_y), G(10))
            mid_x = (hip_x+knee_x)//2; mid_y = (hip_y+knee_y)//2
            pygame.draw.circle(surf, _ab(p["accent"], alpha), (mid_x,mid_y), G(4))
            pygame.draw.circle(surf, _ab(p["metal"], alpha), (knee_x,knee_y), G(9))
            pygame.draw.circle(surf, _ab(_lt(p["metal"],1.5), alpha), (knee_x,knee_y), G(5))
            foot_x = knee_x + sx*G(10); foot_y = cy + G(80)
            pygame.draw.line(surf, _ab(p["limb"], alpha), (knee_x,knee_y), (foot_x,foot_y), G(7))
            for ci in range(3):
                ca = math.radians(200 + ci*22 + sx*30)
                pygame.draw.line(surf, _ab(p["accent"], alpha),
                    (foot_x,foot_y), (foot_x+int(math.cos(ca)*G(16)), foot_y+int(math.sin(ca)*G(16))), G(2))

        # ── Tay servo 2 khớp + vuốt ───────────────────────────
        for sx in [-1, 1]:
            wave = math.sin(t*2.8+sx*0.8)*G(10)
            sh_x = cx+sx*G(30); sh_y = cy-G(75)
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (sh_x,sh_y), G(12))
            pygame.draw.circle(surf, _ab(p["neon"],alpha*0.8), (sh_x,sh_y), G(6))
            pygame.draw.circle(surf, _ab(_lt(p["neon"],1.5),alpha), (sh_x,sh_y), G(2))
            el_x = cx+sx*G(62)+int(wave); el_y = cy-G(48)
            pygame.draw.line(surf, _ab(p["limb"],alpha), (sh_x,sh_y), (el_x,el_y), G(10))
            bx = (sh_x+el_x)//2; by = (sh_y+el_y)//2
            pygame.draw.circle(surf, _ab(p["accent"],alpha), (bx,by), G(4))
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (el_x,el_y), G(10))
            pygame.draw.circle(surf, _ab(_lt(p["metal"],1.4),alpha), (el_x,el_y), G(5))
            wr_x = el_x+sx*G(22); wr_y = el_y+G(28)
            pygame.draw.line(surf, _ab(p["limb"],alpha), (el_x,el_y), (wr_x,wr_y), G(7))
            for ci in range(4):
                ca = math.radians(200+ci*22+sx*(-15))
                pygame.draw.line(surf, _ab(p["neon"],alpha),
                    (wr_x,wr_y), (wr_x+int(math.cos(ca)*G(15)), wr_y+int(math.sin(ca)*G(15))), G(2))

        # ── Thân 4 đốt cơ khí ─────────────────────────────────
        for sw, sh, sy, br in [
            (G(68), G(28), cy-G(100), G(6)),
            (G(75), G(26), cy-G(74),  G(5)),
            (G(72), G(26), cy-G(50),  G(5)),
            (G(65), G(24), cy-G(26),  G(5)),
        ]:
            pygame.draw.rect(surf, _ab(p["body"],alpha), (cx-sw//2,sy,sw,sh), border_radius=br)
            pygame.draw.line(surf, _ab(_lt(p["body"],1.6),alpha*0.4),
                (cx-sw//2+G(4),sy+sh//2), (cx+sw//2-G(4),sy+sh//2), 1)
            pygame.draw.rect(surf, _ab(p["neon"],alpha*0.6), (cx-sw//2,sy,sw,sh), width=1, border_radius=br)
        for sy in [cy-G(73), cy-G(49), cy-G(25)]:
            pygame.draw.rect(surf, _ab(p["metal"],alpha), (cx-G(8),sy-G(3),G(16),G(6)), border_radius=G(2))
            pygame.draw.circle(surf, _ab(p["accent"],alpha), (cx,sy), G(3))
        for ri, am in [(G(16),0.15),(G(10),0.4),(G(5),0.9)]:
            pulse = abs(math.sin(t*4.5))
            gs = pygame.Surface((ri*2,ri*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, _rgba(p["neon"], int(alpha*am*210*pulse)), (ri,ri), ri)
            surf.blit(gs, (cx-ri, cy-G(60)-ri))

        # ── Đầu tam giác cơ khí ───────────────────────────────
        hy = cy - G(178); hw = G(46)
        head_pts = [(cx,hy), (cx-hw,hy+G(48)), (cx+hw,hy+G(48))]
        pygame.draw.polygon(surf, _ab(p["head"],alpha), head_pts)
        pygame.draw.polygon(surf, _ab(_lt(p["head"],0.7),alpha),
            [(cx-hw,hy+G(48)),(cx-G(10),hy+G(15)),(cx-G(10),hy+G(48))])
        pygame.draw.polygon(surf, _ab(_lt(p["head"],0.7),alpha),
            [(cx+hw,hy+G(48)),(cx+G(10),hy+G(15)),(cx+G(10),hy+G(48))])
        pygame.draw.line(surf, _ab(_lt(p["head"],1.6),alpha*0.5), (cx,hy+G(6)), (cx,hy+G(40)), G(3))
        for bx2,by2 in [(cx-G(22),hy+G(35)),(cx+G(22),hy+G(35))]:
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (bx2,by2), G(4))
            pygame.draw.line(surf, _ab(p["accent"],alpha*0.8),(bx2-G(3),by2),(bx2+G(3),by2),1)
            pygame.draw.line(surf, _ab(p["accent"],alpha*0.8),(bx2,by2-G(3)),(bx2,by2+G(3)),1)
        pygame.draw.polygon(surf, _ab(p["neon"],alpha*0.9), head_pts, 2)
        tongue_y = hy+G(48)
        pygame.draw.rect(surf, _ab(p["neon"],alpha), (cx-G(2),tongue_y,G(4),G(10)))
        pygame.draw.line(surf, _ab(p["neon"],alpha),(cx-G(7),tongue_y+G(10)),(cx,tongue_y+G(6)),G(2))
        pygame.draw.line(surf, _ab(p["neon"],alpha),(cx+G(7),tongue_y+G(10)),(cx,tongue_y+G(6)),G(2))
        self._draw_eyes(surf, cx, hy+G(26), G(13), G(9), G(5), alpha)
        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(65),G(58)), body_r=(G(88),G(96)))

    # ══════════════════════════════════════════════════════════
    #   ROBOT 8 — COLOSSUS  (Titan Cơ Giới Khổng Lồ)
    #   Giáp tấm, piston thủy lực, bu lông, khớp cầu
    # ══════════════════════════════════════════════════════════
    def _draw_colossus(self, surf, cx, cy, alpha):
        G = lambda v: int(v * self.scale)
        p = self._pal
        t = self._time
        shake = int(math.sin(t*1.8)*G(2))

        # ── Chân giáp tấm + piston ─────────────────────────────
        for sx in [-1, 1]:
            lx = cx + sx*G(55)
            pt = int(math.sin(t*1.5+sx)*G(8))
            px2 = lx+sx*G(20)
            pygame.draw.rect(surf, _ab(p["metal"],alpha*0.8), (px2-G(4),cy-G(5)+shake,G(8),G(45)+pt), border_radius=G(2))
            pygame.draw.rect(surf, _ab(_lt(p["neon"],0.8),alpha*0.5), (px2-G(2),cy-G(5)+shake,G(4),G(45)+pt), border_radius=G(1))
            pygame.draw.rect(surf, _ab(p["limb"],alpha), (px2-G(7),cy+G(40)+shake,G(14),G(12)), border_radius=G(3))
            pygame.draw.rect(surf, _ab(p["limb"],alpha), (lx-G(30),cy-G(8)+shake,G(60),G(60)), border_radius=G(6))
            for i in range(3):
                pygame.draw.line(surf, _ab(_lt(p["limb"],1.5),alpha*0.4),
                    (lx-G(24),cy+G(4)+i*G(14)+shake),(lx+G(24),cy+G(4)+i*G(14)+shake),1)
            for bx2,by2 in [(lx-G(22),cy-G(2)+shake),(lx+G(22),cy-G(2)+shake),(lx-G(22),cy+G(44)+shake),(lx+G(22),cy+G(44)+shake)]:
                pygame.draw.circle(surf, _ab(p["metal"],alpha),(bx2,by2),G(5))
                pygame.draw.line(surf, _ab(p["accent"],alpha*0.7),(bx2-G(3),by2),(bx2+G(3),by2),1)
                pygame.draw.line(surf, _ab(p["accent"],alpha*0.7),(bx2,by2-G(3)),(bx2,by2+G(3)),1)
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (lx,cy+G(52)+shake), G(18))
            pygame.draw.circle(surf, _ab(_lt(p["metal"],1.3),alpha), (lx,cy+G(52)+shake), G(12))
            pygame.draw.circle(surf, _ab(p["neon"],alpha*0.6), (lx,cy+G(52)+shake), G(6))
            pygame.draw.rect(surf, _ab(p["metal"],alpha), (lx-G(38),cy+G(68)+shake,G(76),G(20)), border_radius=G(5))
            pygame.draw.rect(surf, _ab(p["neon"],alpha*0.4), (lx-G(38),cy+G(68)+shake,G(76),G(20)), width=1, border_radius=G(5))

        # ── Tay búa thủy lực ──────────────────────────────────
        for sx in [-1, 1]:
            sh_x = cx+sx*G(82); sh_y = cy-G(92)
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (sh_x,sh_y), G(24))
            pygame.draw.circle(surf, _ab(_lt(p["metal"],1.4),alpha), (sh_x,sh_y), G(16))
            pygame.draw.circle(surf, _ab(p["neon"],alpha*0.7), (sh_x,sh_y), G(8))
            for pi in [-1,1]:
                px3 = sh_x+pi*G(14)
                plen = G(30)+int(math.sin(t*2+pi+sx)*G(6))
                pygame.draw.rect(surf, _ab(p["limb"],alpha*0.8), (px3-G(4),sh_y,G(8),plen), border_radius=G(2))
                pygame.draw.rect(surf, _ab(p["neon"],alpha*0.3), (px3-G(2),sh_y,G(4),plen), border_radius=G(1))
            el_x = cx+sx*G(110); el_y = cy-G(56)
            arm_pts = [(sh_x,sh_y),(sh_x+sx*G(10),sh_y+G(20)),(el_x+sx*G(10),el_y+G(20)),(el_x,el_y)]
            pygame.draw.polygon(surf, _ab(p["limb"],alpha), arm_pts)
            pygame.draw.polygon(surf, _ab(p["neon"],alpha*0.5), arm_pts, 1)
            bm_x = (sh_x+el_x)//2; bm_y = (sh_y+el_y)//2
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (bm_x,bm_y), G(7))
            pygame.draw.line(surf, _ab(p["accent"],alpha),(bm_x-G(5),bm_y),(bm_x+G(5),bm_y),1)
            pygame.draw.line(surf, _ab(p["accent"],alpha),(bm_x,bm_y-G(5)),(bm_x,bm_y+G(5)),1)
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (el_x,el_y), G(20))
            pygame.draw.circle(surf, _ab(_lt(p["metal"],1.5),alpha), (el_x,el_y), G(13))
            pygame.draw.circle(surf, _ab(p["neon"],alpha*0.8), (el_x,el_y), G(6))
            fx = el_x+sx*G(8); fy = el_y+G(30)
            pygame.draw.rect(surf, _ab(p["body"],alpha), (fx-G(36),fy,G(72),G(62)), border_radius=G(8))
            pygame.draw.rect(surf, _ab(_lt(p["body"],1.3),alpha), (fx-G(36),fy,G(72),G(20)), border_radius=G(6))
            for ki in range(4):
                kx2 = fx-G(24)+ki*G(16); ky2 = fy+G(22)
                pygame.draw.rect(surf, _ab(p["metal"],alpha*0.7), (kx2-G(4),ky2,G(8),G(28)), border_radius=G(3))
                pygame.draw.rect(surf, _ab(p["neon"],alpha*0.4), (kx2-G(2),ky2,G(4),G(28)), border_radius=G(2))
            pygame.draw.rect(surf, _ab(p["neon"],alpha*0.8), (fx-G(36),fy,G(72),G(62)), width=2, border_radius=G(8))

        # ── Thân giáp tấm 3 lớp ───────────────────────────────
        bw,bh = G(180),G(135); bx,by = cx-bw//2, cy-G(142)
        pygame.draw.rect(surf, _ab(p["body"],alpha), (bx,by,bw,bh), border_radius=G(8))
        for i in range(3):
            pw2 = bw-G(20)-i*G(16); ph = G(28)
            px3 = cx-pw2//2; py3 = by+G(8)+i*G(32)
            pygame.draw.rect(surf, _ab(_lt(p["body"],1+i*0.15),alpha), (px3,py3,pw2,ph), border_radius=G(5))
            pygame.draw.line(surf, _ab(_lt(p["body"],1.8),alpha*0.3),(px3+G(6),py3+ph//2),(px3+pw2-G(6),py3+ph//2),1)
        for ri,am in [(G(38),0.1),(G(26),0.25),(G(14),0.7)]:
            pulse = abs(math.sin(t*2))
            gs = pygame.Surface((ri*2,ri*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, _rgba(p["neon"],int(alpha*am*200*pulse)), (ri,ri), ri)
            surf.blit(gs, (cx-ri, cy-G(72)-ri))
        for sx in [-1,1]:
            vx = cx+sx*G(78); vy = by+G(50)
            for vi in range(4):
                pygame.draw.rect(surf, _ab(p["metal"],alpha), (vx-G(8),vy+vi*G(14),G(16),G(8)), border_radius=G(2))
                pygame.draw.rect(surf, _ab(p["neon"],alpha*0.5), (vx-G(6),vy+vi*G(14)+G(2),G(12),G(4)), border_radius=G(1))
        pygame.draw.rect(surf, _ab(p["neon"],alpha*0.8), (bx,by,bw,bh), width=2, border_radius=G(8))
        for bp in [(bx+G(10),by+G(10)),(bx+bw-G(10),by+G(10)),(bx+G(10),by+bh-G(10)),(bx+bw-G(10),by+bh-G(10))]:
            pygame.draw.circle(surf, _ab(p["accent"],alpha), bp, G(6))
            pygame.draw.line(surf, _ab((200,200,200),alpha*0.6),(bp[0]-G(4),bp[1]),(bp[0]+G(4),bp[1]),1)
            pygame.draw.line(surf, _ab((200,200,200),alpha*0.6),(bp[0],bp[1]-G(4)),(bp[0],bp[1]+G(4)),1)

        # ── Đầu lục giác giáp tấm ─────────────────────────────
        hw = G(115); hh = G(90); hy = cy-G(196)
        head_pts = [(cx,hy),(cx+hw//2,hy+G(22)),(cx+hw//2,hy+G(65)),(cx,hy+hh),(cx-hw//2,hy+G(65)),(cx-hw//2,hy+G(22))]
        pygame.draw.polygon(surf, _ab(p["head"],alpha), head_pts)
        inner = [(cx,hy+G(8)),(cx+G(42),hy+G(25)),(cx+G(38),hy+G(58)),(cx,hy+hh-G(8)),(cx-G(38),hy+G(58)),(cx-G(42),hy+G(25))]
        pygame.draw.polygon(surf, _ab(_lt(p["head"],1.2),alpha*0.5), inner)
        for bp in head_pts[1::2]:
            bpx,bpy = int(bp[0]),int(bp[1])
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (bpx,bpy), G(5))
            pygame.draw.line(surf, _ab(p["accent"],alpha*0.8),(bpx-G(3),bpy),(bpx+G(3),bpy),1)
        pygame.draw.polygon(surf, _ab(p["neon"],alpha*0.9), head_pts, 2)
        self._draw_eyes(surf, cx, hy+G(44), G(25), G(14), G(8), alpha)
        pygame.draw.line(surf, _ab(p["metal"],alpha),(cx-G(20),hy),(cx-G(15),hy-G(22)),G(4))
        pygame.draw.circle(surf, _ab(p["neon"],alpha),(cx-G(15),hy-G(22)),G(5))
        pygame.draw.line(surf, _ab(p["metal"],alpha),(cx+G(20),hy),(cx+G(15),hy-G(18)),G(4))
        pygame.draw.circle(surf, _ab(p["accent"],alpha),(cx+G(15),hy-G(18)),G(5))
        for ri in [G(50),G(70),G(90)]:
            fa = int(alpha*20*abs(math.sin(t*1.5)))
            gs = pygame.Surface((ri*2,ri//3), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, _rgba(p["neon"],fa), gs.get_rect())
            surf.blit(gs, (cx-ri, cy+G(78)))
        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(136),G(100)), body_r=(G(195),G(146)))

    # ══════════════════════════════════════════════════════════
    #   ROBOT 9 — ABYSS  (Đơn Vị Bóng Tối Cơ Khí)
    #   Khung giáp xương, sensor mảng, cánh năng lượng
    # ══════════════════════════════════════════════════════════
    def _draw_abyss(self, surf, cx, cy, alpha):
        G = lambda v: int(v * self.scale)
        p = self._pal
        t = self._time
        float_off = int(math.sin(t*1.1)*G(7))

        # ── Vòng hào quang năng lượng ─────────────────────────
        for ri_b, spd, thk in [(G(105),1.2,2),(G(130),0.8,1)]:
            a_ring = int(alpha*40*abs(math.sin(t*1.1+ri_b*0.01)))
            if a_ring > 3:
                rs = pygame.Surface((ri_b*2+6,ri_b//2+6), pygame.SRCALPHA)
                pygame.draw.ellipse(rs, _rgba(p["neon"],a_ring), rs.get_rect(), thk)
                surf.blit(rs, (cx-ri_b-3, cy-G(75)+float_off-rs.get_height()//2))

        # ── Chân khung xương ──────────────────────────────────
        for sx in [-1, 1]:
            lx = cx+sx*G(32); ly_t = cy+G(6)+float_off
            pygame.draw.line(surf, _ab(p["limb"],alpha), (lx,ly_t), (lx+sx*G(8),cy+G(50)+float_off), G(9))
            pygame.draw.line(surf, _ab(p["neon"],alpha*0.4), (lx,ly_t), (lx+sx*G(8),cy+G(50)+float_off), G(3))
            kx = lx+sx*G(8); ky = cy+G(50)+float_off
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (kx,ky), G(11))
            pygame.draw.circle(surf, _ab(p["neon"],alpha*0.7), (kx,ky), G(5))
            pygame.draw.line(surf, _ab(p["limb"],alpha), (kx,ky), (kx+sx*G(4),cy+G(85)+float_off), G(7))
            fx = kx+sx*G(4); fy = cy+G(85)+float_off
            pygame.draw.rect(surf, _ab(p["metal"],alpha), (fx-G(14),fy,G(28),G(14)), border_radius=G(3))
            pygame.draw.rect(surf, _ab(p["neon"],alpha*0.5), (fx-G(14),fy,G(28),G(14)), width=1, border_radius=G(3))

        # ── Tay xương khung + sensor ───────────────────────────
        for sx in [-1, 1]:
            sh_x = cx+sx*G(36); sh_y = cy-G(72)+float_off
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (sh_x,sh_y), G(12))
            pygame.draw.circle(surf, _ab(p["neon"],alpha*0.7), (sh_x,sh_y), G(6))
            el_x = cx+sx*G(70)+int(math.sin(t*1.5+sx)*G(8)); el_y = cy-G(48)+float_off
            pygame.draw.line(surf, _ab(p["limb"],alpha), (sh_x,sh_y), (el_x,el_y), G(8))
            pygame.draw.line(surf, _ab(p["neon"],alpha*0.35), (sh_x,sh_y), (el_x,el_y), G(3))
            for fi in range(2):
                frac = (fi+1)/3
                fx2 = int(sh_x+(el_x-sh_x)*frac); fy2 = int(sh_y+(el_y-sh_y)*frac)
                pygame.draw.circle(surf, _ab(p["accent"],alpha), (fx2,fy2), G(4))
            pygame.draw.circle(surf, _ab(p["metal"],alpha), (el_x,el_y), G(10))
            pygame.draw.circle(surf, _ab(p["neon"],alpha*0.8), (el_x,el_y), G(5))
            wr_x = el_x+sx*G(20); wr_y = el_y+G(25)+float_off
            pygame.draw.line(surf, _ab(p["limb"],alpha), (el_x,el_y), (wr_x,wr_y), G(7))
            pygame.draw.rect(surf, _ab(p["body"],alpha), (wr_x-G(12),wr_y-G(5),G(24),G(14)), border_radius=G(4))
            for si in range(3):
                sx3 = wr_x-G(6)+si*G(6); sy3 = wr_y-G(1)
                pygame.draw.circle(surf, _ab(p["neon"],alpha), (sx3,sy3), G(2))
                a_s = int(alpha*100*abs(math.sin(t*3+si)))
                if a_s > 5:
                    gs = pygame.Surface((G(4),G(12)), pygame.SRCALPHA)
                    gs.fill(_rgba(p["neon"],a_s))
                    surf.blit(gs, (sx3-G(2),sy3+G(4)))

        # ── Cánh năng lượng ───────────────────────────────────
        for sx in [-1, 1]:
            base_x = cx+sx*G(42); base_y = cy-G(85)+float_off
            for wi in range(2):
                angle = math.radians(-75+sx*(25+wi*30)+math.sin(t*1.5)*8)
                length = G(75-wi*22)
                tip_x = int(base_x+math.cos(angle)*length)
                tip_y = int(base_y+math.sin(angle)*length)
                pygame.draw.line(surf, _ab(p["metal"],alpha), (base_x,base_y), (tip_x,tip_y), G(5))
                pygame.draw.line(surf, _ab(p["neon"],alpha*(0.5-wi*0.1)), (base_x,base_y), (tip_x,tip_y), G(2))
                mid_x = (base_x+tip_x)//2; mid_y = (base_y+tip_y)//2
                perp_a = angle+math.pi/2; pw = G(14-wi*4)
                pts3 = [(base_x,base_y),(tip_x,tip_y),(mid_x+int(math.cos(perp_a)*pw),mid_y+int(math.sin(perp_a)*pw))]
                a_wing = int(alpha*40*abs(math.sin(t*1.5+wi)))
                if a_wing > 3:
                    ws2 = pygame.Surface((SCREEN_W,SCREEN_H), pygame.SRCALPHA)
                    pygame.draw.polygon(ws2, _rgba(p["neon"],a_wing), pts3)
                    surf.blit(ws2, (0,0))
                pygame.draw.circle(surf, _ab(p["neon"],alpha), (tip_x,tip_y), G(4))

        # ── Thân khung giáp ───────────────────────────────────
        bw,bh = G(108),G(112); bx,by = cx-bw//2, cy-G(116)+float_off
        pygame.draw.rect(surf, _ab(p["body"],alpha), (bx,by,bw,bh), border_radius=G(8))
        for sx in [-1,1]:
            px2 = cx+sx*G(22); pw2 = G(34); ph = G(70)
            pygame.draw.rect(surf, _ab(_lt(p["body"],1.2),alpha), (px2-pw2//2,by+G(10),pw2,ph), border_radius=G(5))
            for ri2 in range(3):
                rx = px2-pw2//2+G(6)+ri2*G(10)
                pygame.draw.line(surf, _ab(p["neon"],alpha*0.3),(rx,by+G(14)),(rx,by+G(74)),1)
        for si in range(4):
            sx2 = cx-G(30)+si*G(20); sy2 = by+bh-G(28)
            pygame.draw.rect(surf, _ab(p["metal"],alpha), (sx2-G(6),sy2,G(12),G(18)), border_radius=G(2))
            a_sens = int(alpha*200*abs(math.sin(t*2+si)))
            if a_sens > 5:
                pygame.draw.rect(surf, _ab(p["neon"],a_sens//255), (sx2-G(4),sy2+G(2),G(8),G(14)), border_radius=G(2))
        for ri,am in [(G(28),0.08),(G(18),0.2),(G(9),0.65)]:
            pulse = 0.5+0.5*math.sin(t*3.5)
            gs = pygame.Surface((ri*2,ri*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, _rgba(p["neon"],int(alpha*am*220*pulse)), (ri,ri), ri)
            surf.blit(gs, (cx-ri, cy-G(58)+float_off-ri))
        pygame.draw.rect(surf, _ab(p["neon"],alpha*0.75), (bx,by,bw,bh), width=2, border_radius=G(8))
        for bp in [(bx+G(9),by+G(9)),(bx+bw-G(9),by+G(9)),(bx+G(9),by+bh-G(9)),(bx+bw-G(9),by+bh-G(9))]:
            pygame.draw.circle(surf, _ab(p["accent"],alpha), bp, G(5))
            pygame.draw.line(surf, _ab((180,180,200),alpha*0.5),(bp[0]-G(3),bp[1]),(bp[0]+G(3),bp[1]),1)
            pygame.draw.line(surf, _ab((180,180,200),alpha*0.5),(bp[0],bp[1]-G(3)),(bp[0],bp[1]+G(3)),1)

        # ── Đầu cầu sensor ────────────────────────────────────
        hr = G(52); hy = cy-G(174)+float_off
        pygame.draw.circle(surf, _ab(p["head"],alpha), (cx,hy), hr)
        pygame.draw.circle(surf, _ab(_lt(p["head"],1.25),alpha), (cx,hy), int(hr*0.7))
        for i in range(8):
            sa = t*1.5+i*math.pi/4
            sx3 = cx+int(math.cos(sa)*G(48)); sy3 = hy+int(math.sin(sa)*G(20))
            a_s2 = int(alpha*(0.4+0.6*abs(math.sin(t*2+i)))*160)
            pygame.draw.circle(surf, _ab(p["neon"],a_s2//255), (sx3,sy3), G(4))
        for ex,ey in [(cx-G(16),hy-G(8)),(cx+G(16),hy-G(8)),(cx,hy+G(12))]:
            pygame.draw.circle(surf, _ab((5,5,12),alpha), (ex,ey), G(8))
            ec = tuple(min(255,int(p["eye"][c]*(0.6+0.4*abs(math.sin(t*2.2))))) for c in range(3))
            pygame.draw.circle(surf, _ab(ec,alpha), (ex,ey), G(5))
            gs = pygame.Surface((G(20),G(20)), pygame.SRCALPHA)
            pygame.draw.circle(gs, _rgba(p["eye"],int(alpha*70)), (G(10),G(10)), G(10))
            surf.blit(gs, (ex-G(10),ey-G(10)))
        for ai,ax2 in enumerate([cx-G(28),cx-G(14),cx+G(14),cx+G(28)]):
            al2 = G(16+ai%2*6)
            pygame.draw.line(surf, _ab(p["metal"],alpha), (ax2,hy-hr), (ax2,hy-hr-al2), G(3))
            a_led = int(alpha*200*abs(math.sin(t*3+ai)))
            pygame.draw.circle(surf, _ab(p["neon"],a_led//255), (ax2,hy-hr-al2), G(3))
        pygame.draw.circle(surf, _ab(p["neon"],int(alpha*190*abs(math.sin(t*2)))), (cx,hy), hr, 2)
        self._draw_common_neon_glow(surf, cx, cy, alpha,
            head_r=(G(122),G(112)), body_r=(G(122),G(122)))


def _dk(c, f):
    return tuple(max(0, int(x*f)) for x in c[:3])

def _lt(c, f):
    return tuple(min(255, int(x*f)) for x in c[:3])

def _ab(c, a):
    return tuple(max(0, min(255, int(x*max(0.0,min(1.0,a))))) for x in c[:3])

def _rgba(c, a):
    """Safe RGBA tuple — clamps tất cả giá trị vào [0, 255]."""
    return (
        max(0, min(255, int(c[0]))),
        max(0, min(255, int(c[1]))),
        max(0, min(255, int(c[2]))),
        max(0, min(255, int(a))),
    )