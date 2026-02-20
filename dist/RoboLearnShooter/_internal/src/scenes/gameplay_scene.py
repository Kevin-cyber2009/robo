"""
gameplay_scene.py - CINEMATIC FPS Gameplay :))))
============================================
"""

import pygame
import math
import random
from src.scenes.base_scene import BaseScene
from src.constants import *
from src.assets import assets
from src.ui_components import HealthBar, draw_crosshair
from src.robot_renderer import RobotRenderer
from src.question_overlay import QuestionOverlay
from src.question_manager import QuestionManager
from src.powerup_system import PowerupSystem


# ─── Màu FPS Environment ─────────────────────────────────────
ENV_CEILING   = (8,   10,  20)
ENV_FLOOR     = (14,  18,  32)
ENV_GRID_LINE = (22,  30,  55)
ENV_NEON_LINE = (0,   80,  160)
ENV_HORIZON   = (18,  28,  55)
ENV_FOG       = (10,  14,  28)


class GameplayScene(BaseScene):

    # Thứ tự robot (0-9), sau đó lặp lại từ đầu
    ROBOT_ORDER  = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # HP bonus từng robot (index 0-9)
    ROBOT_HP_BONUS = [0, 50, -20, 30, -10, 80, 120, -30, 150, 80]
    # Map theo round: 3 map luân phiên (sau mỗi 10 robot = 1 round)
    MAP_NAMES    = ["lab", "space", "jungle"]

    def __init__(self, screen, manager):
        super().__init__(screen, manager)

        self._q_manager = QuestionManager()
        n = self._q_manager.load_files(self.state.selected_question_files)
        if n == 0:
            manager.go_to(SCENE_MENU)
            return

        # === Wave / Robot hệ thống ===
        self._wave_index    = 0          # Vị trí trong ROBOT_ORDER (tăng mãi)
        self._robots_killed = 0          # Tổng robot đã giết
        self._total_waves   = 10         # Tổng 10 loại robot

        # === Map system ===
        self._round         = 0          # Round hiện tại (0-indexed), tăng sau mỗi 10 robot
        self._current_map   = 0          # Index trong MAP_NAMES (0=lab, 1=space, 2=jungle)
        self._map_transition_t = 0.0     # 0 = không transition
        self._map_transition_phase = "none"  # "out"|"in"|"none"

        # Màn chuyển tiếp
        self._transition_t  = 0.0       # 0 = đang chơi, >0 = đang chuyển
        self._transition_phase = "none" # "out" | "in" | "none"
        self._next_robot_idx = 0

        # Khởi tạo robot đầu tiên
        self._spawn_robot(0)

        self._overlay   = QuestionOverlay(screen)
        self._cur_zone  = None
        self._cur_q     = None

        # --- Gun state ---
        self._gun_recoil    = 0.0
        self._gun_sway_x    = 0.0
        self._gun_sway_y    = 0.0
        self._prev_mouse    = pygame.mouse.get_pos()

        # --- Camera shake ---
        self._shake_x       = 0.0
        self._shake_y       = 0.0
        self._shake_decay   = 0.0

        # --- FX ---
        self._muzzle_t      = 0.0
        self._muzzle_shells = []
        self._crosshair_t   = 0.0
        self._aim_on_robot  = False
        self._vignette_t    = 0.0

        # --- Game state ---
        self._time          = 0.0
        self._game_over     = False
        self._game_win      = False   # Không dùng nữa (game vô tận)
        self._wrong_count   = 0
        self._correct_count = 0
        self._score         = 0
        self._history       = []
        self._dmg_numbers   = []

        # Hiển thị banner tên robot khi vào
        self._robot_banner_t  = 3.0    # Đếm ngược banner

        # ── COMBO SYSTEM ──────────────────────────────────────
        self._combo          = 0       # Streak trả lời đúng liên tiếp
        self._combo_max      = 0       # Combo cao nhất
        self._combo_timer    = 0.0     # Hiệu ứng hiển thị combo
        self._combo_notifs   = []      # [(text,color,y,life)]

        # ── POWER-UP SYSTEM ───────────────────────────────────
        self._powerups = PowerupSystem()

        # ── COUNTDOWN MODE ────────────────────────────────────
        self._countdown_mode = getattr(self.state, "countdown_mode", False)
        # Intro countdown: 3s nếu Time Attack, 0 nếu Normal
        self._intro_t = 3.0 if self._countdown_mode else 0.0

        # --- Env decorations ---
        self._wall_lights   = self._gen_wall_lights()
        self._floor_tiles   = self._gen_floor_tiles()

        pygame.mouse.set_visible(False)

    # ─── Robot Wave Management ────────────────────────────────

    def _get_robot_idx(self, wave_index: int) -> int:
        """Lấy robot index (0-6) theo wave, lặp lại sau 7."""
        return self.ROBOT_ORDER[wave_index % self._total_waves]

    def _get_robot_hp(self, wave_index: int) -> float:
        """HP robot tăng theo vòng lặp."""
        robot_idx  = self._get_robot_idx(wave_index)
        base_hp    = float(ROBOT_MAX_HP + self.ROBOT_HP_BONUS[robot_idx])
        cycle      = wave_index // self._total_waves   # Số vòng đã qua
        bonus      = cycle * 60   # Mỗi vòng lặp HP tăng thêm 60
        return base_hp + bonus

    def _spawn_robot(self, wave_index: int):
        """Tạo robot mới theo wave index."""
        robot_idx        = self._get_robot_idx(wave_index)
        robot_x          = SCREEN_W // 2
        robot_y          = SCREEN_H // 2 + 55
        self._robot      = RobotRenderer(robot_x, robot_y, scale=1.7,
                                          robot_index=robot_idx)
        self._robot_hp   = self._get_robot_hp(wave_index)
        self._robot_max_hp = self._robot_hp

        # HP bar cập nhật màu theo robot
        self._hp_bar = HealthBar(SCREEN_W // 2 - 200, 22, 400, 26)
        self._hp_bar.set_ratio(self._robot_hp, self._robot_max_hp)
        self._robot_banner_t = 3.0

    def _trigger_next_robot(self):
        """Gọi khi robot hiện tại chết → bắt đầu chuyển cảnh."""
        self._transition_phase = "out"
        self._transition_t     = 0.0
        self._wave_index      += 1
        self._robots_killed   += 1
        self._score           += 200   # Bonus điểm giết robot

        # Kiểm tra đủ 10 robot = xong 1 round → đổi map
        if self._robots_killed > 0 and self._robots_killed % self._total_waves == 0:
            next_round = self._robots_killed // self._total_waves
            self._current_map = next_round % len(self.MAP_NAMES)
            self._round = next_round
            # Trigger map transition (đè lên robot transition)
            self._map_transition_phase = "out"
            self._map_transition_t = 0.0
            # Regenerate environment for new map
            self._wall_lights = self._gen_wall_lights()
            self._floor_tiles = self._gen_floor_tiles()

    def _cleanup(self):
        pygame.mouse.set_visible(True)

    # ─── Environment generators ───────────────────────────────

    def _gen_wall_lights(self):
        lights = []
        for i in range(6):
            lights.append({
                "x": int(80 + i * (SCREEN_W - 160) / 5),
                "y": random.randint(40, 100),
                "flicker": random.uniform(0, math.pi * 2),
                "intensity": random.uniform(0.6, 1.0),
                "color": random.choice([(0, 140, 255), (0, 200, 140), (160, 60, 255)]),
            })
        return lights

    def _gen_floor_tiles(self):
        """Các tile sàn phát sáng ngẫu nhiên."""
        tiles = []
        horizon = SCREEN_H // 2
        for i in range(12):
            angle   = (i - 5.5) * 0.14
            base_x  = SCREEN_W // 2 + int(math.tan(angle) * (SCREEN_H - horizon))
            tiles.append({
                "base_x": base_x,
                "phase": random.uniform(0, math.pi * 2),
            })
        return tiles

    # ─── Update ───────────────────────────────────────────────

    def update(self, dt, events):
        self._time += dt

        # ── Intro countdown (Time Attack mode) ─────────────────
        if self._intro_t > 0:
            self._intro_t = max(0.0, self._intro_t - dt)
            for ev in events:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.manager.go_to(SCENE_MENU)
            self._robot.update(dt)
            return

        if self._game_over:
            self._update_endscreen(dt, events)
            return

        # === TRANSITION giữa các robot ===
        if self._transition_phase != "none":
            self._update_transition(dt)
            self._robot.update(dt)
            return

        # === MAP TRANSITION (độc lập với robot transition) ===
        if self._map_transition_phase != "none":
            self._update_map_transition(dt)
            self._robot.update(dt)
            return

        self._robot.update(dt)
        self._hp_bar.update(dt)

        # Banner đếm ngược
        self._robot_banner_t = max(0.0, self._robot_banner_t - dt)

        # Crosshair aim detection
        mx, my = pygame.mouse.get_pos()
        self._aim_on_robot = self._robot.check_hit(mx, my) is not None

        # Mouse sway cho gun
        pmx, pmy = self._prev_mouse
        self._gun_sway_x += (mx - pmx) * 0.04
        self._gun_sway_y += (my - pmy) * 0.04
        self._gun_sway_x *= 0.85
        self._gun_sway_y *= 0.85
        self._prev_mouse = (mx, my)

        # FX decay
        self._gun_recoil  = max(0.0, self._gun_recoil  - dt * 10)
        self._muzzle_t    = max(0.0, self._muzzle_t    - dt * 14)
        self._crosshair_t = max(0.0, self._crosshair_t - dt * 5)
        self._vignette_t  = max(0.0, self._vignette_t  - dt * 1.2)

        # Camera shake
        self._shake_decay = max(0.0, self._shake_decay - dt * 8)
        self._shake_x *= 0.75
        self._shake_y *= 0.75

        # Muzzle shells
        for sh in self._muzzle_shells[:]:
            sh["life"] -= dt * 2
            sh["x"]    += sh["vx"] * dt * 60
            sh["y"]    += sh["vy"] * dt * 60
            sh["vy"]   += 0.4
            sh["rot"]  += sh["rot_spd"] * dt
            if sh["life"] <= 0:
                self._muzzle_shells.remove(sh)

        # Damage numbers
        for dn in self._dmg_numbers[:]:
            dn["life"] -= dt
            dn["y"]    += dn["vy"] * dt
            dn["vy"]   *= 0.92
            if dn["life"] <= 0:
                self._dmg_numbers.remove(dn)

        # Question overlay
        result = self._overlay.update(dt, events)
        if result is not None:
            self._process_answer(result)

        # Power-up update + collect
        if not self._overlay.is_visible:
            collected = self._powerups.update(dt, events)
            for kind in collected:
                if kind == "heal":
                    self._wrong_count = max(0, self._wrong_count - 1)
                    self._spawn_combo_notif("+1 MÁU", (220,60,80))

        # Combo notifs
        for n in self._combo_notifs[:]:
            n["life"] -= dt
            n["y"]    -= dt * 35
            if n["life"] <= 0: self._combo_notifs.remove(n)

        # Input
        if not self._overlay.is_visible:
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._do_shoot(ev.pos)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self._go_to_result()

    def _update_transition(self, dt: float):
        """
        Màn chuyển tiếp giữa các robot:
        phase "out": màn tối dần (0.8s) rồi spawn robot mới
        phase "in":  màn sáng lên (0.6s)
        """
        FADE_OUT_DUR = 0.8
        FADE_IN_DUR  = 0.7

        self._transition_t += dt

        if self._transition_phase == "out":
            if self._transition_t >= FADE_OUT_DUR:
                # Spawn robot mới
                self._spawn_robot(self._wave_index)
                self._transition_phase = "in"
                self._transition_t     = 0.0
                # Tăng shake nhẹ
                self._shake_x  = random.uniform(-12, 12)
                self._shake_y  = random.uniform(-6, 6)
                self._shake_decay = 1.0

        elif self._transition_phase == "in":
            if self._transition_t >= FADE_IN_DUR:
                self._transition_phase = "none"
                self._transition_t     = 0.0

    def _do_shoot(self, pos):
        if self._game_over:
            return
        # Hiệu ứng bắn
        self._gun_recoil  = 1.0
        self._muzzle_t    = 1.0
        self._crosshair_t = 1.0
        self._shake_x     = random.uniform(-6, 6)
        self._shake_y     = random.uniform(-5, -2)
        self._spawn_shell()

        zone = self._robot.check_hit(pos[0], pos[1])
        if zone:
            q = self._q_manager.get_question_for_zone(zone)
            if q:
                self._cur_zone = zone
                self._cur_q    = q
                # Power-up checks
                slow = self._powerups.consume_slow_time()
                hint = self._powerups.consume_hint()
                self._overlay.show(q, zone, slow_time=slow, hint_reveal=hint,
                                   use_timer=self._countdown_mode)
                # Maybe drop item on robot hit
                self._powerups.maybe_drop(self._robot.cx, self._robot.cy)

    def _process_answer(self, is_correct):
        zone = self._cur_zone
        q    = self._cur_q
        self._history.append({
            "question": q["question"],
            "type": q["type"],
            "zone": zone,
            "correct": is_correct,
        })

        if is_correct:
            dmg  = {ZONE_HEAD_KEY: DAMAGE_HEAD, ZONE_BODY_KEY: DAMAGE_BODY, ZONE_LIMB_KEY: DAMAGE_LIMB}.get(zone, 40)
            pts  = {ZONE_HEAD_KEY: SCORE_HEAD,  ZONE_BODY_KEY: SCORE_BODY,  ZONE_LIMB_KEY: SCORE_LIMB}.get(zone, 100)

            # Speed bonus từ overlay (chỉ áp dụng trong Time Attack mode)
            speed_mult = getattr(self._overlay, "last_score_mult", 1.0) if self._countdown_mode else 1.0

            # Double score power-up
            if self._powerups.double_score_active:
                speed_mult *= 2.0

            # Combo bonus
            self._combo += 1
            self._combo_max = max(self._combo_max, self._combo)
            self._combo_timer = 2.5
            combo_mult = min(1.0 + (self._combo - 1) * 0.2, 3.0)  # x1 → x3 max ở combo 11+
            total_mult = speed_mult * combo_mult

            final_pts = int(pts * total_mult)
            self._robot_hp -= dmg
            self._robot_hp  = max(0.0, self._robot_hp)
            self._score    += final_pts
            self._correct_count += 1
            self._robot.trigger_hit(zone)
            self._hp_bar.set_ratio(self._robot_hp, self._robot_max_hp)
            self._spawn_dmg_number(final_pts, zone, total_mult)

            # Combo notif
            if self._combo >= 2:
                colors = [(255,200,60),(255,140,30),(255,80,80),(200,60,255),(60,220,255)]
                cc = colors[min(self._combo-2, len(colors)-1)]
                self._spawn_combo_notif(f"COMBO ×{self._combo}!", cc)
            elif speed_mult >= 2.0:
                self._spawn_combo_notif("SPEED BONUS ×2!", (255,230,50))

            if self._robot_hp <= 0:
                self._robot.trigger_death()
                self._trigger_next_robot()
        else:
            # Shield absorbs one wrong answer
            if self._powerups.consume_shield():
                self._spawn_combo_notif("SHIELD!", (80,160,255))
            else:
                self._combo = 0   # Reset combo
                self._wrong_count += 1
                self._vignette_t   = 1.5
                if self._wrong_count >= MAX_WRONG_ANSWERS:
                    self._game_over = True

        self._cur_zone = None
        self._cur_q    = None

    def _update_endscreen(self, dt, events):
        self._robot.update(dt)
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_to_result()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self._go_to_result()

    def _go_to_result(self):
        self._cleanup()
        self.state.current_score       = self._score
        self.state.correct_count       = self._correct_count
        self.state.wrong_count         = self._wrong_count
        self.state.answered_questions  = self._history
        self.state.combo_max           = self._combo_max
        self.manager.go_to(SCENE_RESULT)

    def _spawn_combo_notif(self, text, color):
        self._combo_notifs.append({
            "text": text, "color": color,
            "y": float(SCREEN_H // 2 - 60), "life": 2.0
        })

    def _spawn_shell(self):
        """Vỏ đạn bay ra phải."""
        gx = SCREEN_W - 200
        gy = SCREEN_H - 220
        self._muzzle_shells.append({
            "x": float(gx - 20),
            "y": float(gy),
            "vx": random.uniform(3, 6),
            "vy": random.uniform(-5, -2),
            "rot": 0.0,
            "rot_spd": random.uniform(180, 540),
            "life": 1.0,
        })

    def _spawn_dmg_number(self, pts, zone, mult=1.0):
        zone_y = {ZONE_HEAD_KEY: self._robot.cy - 175,
                  ZONE_BODY_KEY: self._robot.cy - 80,
                  ZONE_LIMB_KEY: self._robot.cy + 30}
        y = zone_y.get(zone, self._robot.cy)
        is_crit = (zone == ZONE_HEAD_KEY)
        is_bonus = mult > 1.05
        text = f"+{pts}"
        if mult >= 2.0: text += " "
        elif is_crit: text += "!!"
        self._dmg_numbers.append({
            "text":  text,
            "x":     float(self._robot.cx + random.randint(-40, 40)),
            "y":     float(y),
            "vy":    -90,
            "life":  1.8,
            "color": (255, 220, 50) if is_bonus else ((255, 60, 60) if is_crit else (255, 180, 50)),
            "size":  "lg" if (is_crit or is_bonus) else "md",
        })

    # ─── Draw ─────────────────────────────────────────────────

    def draw(self):
        sx = int(self._shake_x * self._shake_decay)
        sy = int(self._shake_y * self._shake_decay)

        buf = pygame.Surface((SCREEN_W, SCREEN_H))
        buf.fill(ENV_CEILING)

        self._draw_environment(buf)
        self._robot.draw(buf)
        self._draw_muzzle_light(buf)
        self._draw_damage_numbers(buf)
        self._powerups.draw(buf, self._time)     # Power-up floating items
        self._draw_combo_hud(buf)                 # Combo meter
        self._draw_gun(buf)
        self._draw_shells(buf)
        self._draw_hud(buf)
        self._powerups.draw_hud(buf)              # Active buff icons

        self.screen.blit(buf, (sx, sy))

        self._draw_vignette()
        self._draw_scanlines()
        self._draw_crosshair_custom()

        # Death flash effect khi robot vừa chết
        if self._robot.is_dead and getattr(self._robot, "_death_flash", False):
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((255,255,255, 80))
            self.screen.blit(flash, (0,0))
            self._robot._death_flash = False  # Consume once

        # Combo notifs (trên overlay)
        for n in self._combo_notifs:
            a = min(255, int(n["life"]/2.0 * 255))
            ns = assets.render_text(n["text"], "lg", n["color"], bold=True,
                                    shadow=True, shadow_color=(0,0,0))
            ns.set_alpha(a)
            self.screen.blit(ns, (SCREEN_W//2 - ns.get_width()//2, int(n["y"])))

        # Overlay câu hỏi
        self._overlay.draw()

        # Transition fade giữa các robot
        if self._transition_phase != "none":
            self._draw_transition()

        # Map transition (đè lên robot transition, hiện tên map mới)
        if self._map_transition_phase != "none":
            self._draw_map_transition()

        # Robot name banner
        if self._robot_banner_t > 0:
            self._draw_robot_banner()

        # Intro countdown overlay (Time Attack mode)
        if self._intro_t > 0:
            self._draw_intro_countdown()

        if self._game_over:
            self._draw_endscreen()

    def _draw_intro_countdown(self):
        """Màn đếm ngược 3 giây cho Time Attack mode."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 10, 190))
        self.screen.blit(overlay, (0, 0))

        t = self._intro_t
        cy = SCREEN_H // 2

        # Mode title
        mt = assets.render_text("TIME ATTACK", "xl", (255, 200, 40), bold=True, shadow=True)
        self.screen.blit(mt, (SCREEN_W//2 - mt.get_width()//2, cy - 140))

        # Rule hints
        hints = [
            "Mỗi câu hỏi có đồng hồ đếm ngược",
            "Trả lời nhanh trong 3 giây → Speed Bonus ×2.0",
            "Trả lời trong 40% thời gian → Speed Bonus ×1.5",
        ]
        for i, h in enumerate(hints):
            hs = assets.render_text(h, "sm", (200, 220, 255), shadow=True)
            self.screen.blit(hs, (SCREEN_W//2 - hs.get_width()//2, cy - 65 + i * 34))

        # Countdown number
        count = max(1, int(t + 0.99))
        pulse = 0.88 + 0.12 * math.sin(self._time * 8)
        colors_cnt = {3: (80, 220, 80), 2: (255, 200, 40), 1: (255, 60, 60)}
        cc = colors_cnt.get(count, (255, 255, 255))
        cs = assets.render_text(str(count), "xl", cc, bold=True, shadow=True)
        cw = max(1, int(cs.get_width() * pulse))
        ch = max(1, int(cs.get_height() * pulse))
        cs2 = pygame.transform.scale(cs, (cw, ch))
        self.screen.blit(cs2, (SCREEN_W//2 - cw//2, cy + 48))

        sub = assets.render_text("Chuẩn bị...", "sm", (140, 150, 180))
        self.screen.blit(sub, (SCREEN_W//2 - sub.get_width()//2, cy + 145))

    def _update_map_transition(self, dt):
        MAP_FADE = 1.8
        self._map_transition_t += dt
        if self._map_transition_phase == "out":
            if self._map_transition_t >= MAP_FADE:
                self._map_transition_phase = "in"
                self._map_transition_t = 0.0
        elif self._map_transition_phase == "in":
            if self._map_transition_t >= MAP_FADE:
                self._map_transition_phase = "none"
                self._map_transition_t = 0.0

    def _draw_map_transition(self):
        """Màn chuyển map: fade đen + tên map mới."""
        MAP_FADE = 1.8
        map_names_display = ["PHÒNG THÍ NGHIỆM", "TRẠM VŨ TRỤ", "RỪNG NEON"]
        map_subtitles = ["LAB — Round mới bắt đầu!", "SPACE STATION — Kẻ thù mạnh hơn!", "JUNGLE BASE — Nguy hiểm tăng cao!"]
        map_colors = [(0,200,80), (60,140,255), (40,220,80)]

        if self._map_transition_phase == "out":
            progress = min(1.0, self._map_transition_t / MAP_FADE)
        else:
            progress = max(0.0, 1.0 - self._map_transition_t / MAP_FADE)

        a = int(progress * 255)
        if a <= 0: return
        fade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fade.fill((0,0,0,a))
        self.screen.blit(fade, (0,0))

        if progress > 0.5:
            text_a = int((progress-0.5)/0.5 * 255)
            mid = self._current_map
            mc = map_colors[mid]
            round_s = assets.render_text(f"ROUND {self._round + 1}", "md", (180,180,200), bold=True)
            round_s.set_alpha(text_a)
            self.screen.blit(round_s, (SCREEN_W//2-round_s.get_width()//2, SCREEN_H//2-80))
            name_s = assets.render_text(map_names_display[mid], "xl", mc, bold=True)
            name_s.set_alpha(text_a)
            self.screen.blit(name_s, (SCREEN_W//2-name_s.get_width()//2, SCREEN_H//2-30))
            sub_s = assets.render_text(map_subtitles[mid], "sm", (200,200,220))
            sub_s.set_alpha(text_a)
            self.screen.blit(sub_s, (SCREEN_W//2-sub_s.get_width()//2, SCREEN_H//2+50))

    def _draw_combo_hud(self, surf):
        """Combo meter ở góc trên phải."""
        if self._combo < 2: return
        t = self._time
        # Màu theo combo
        colors = [(255,200,50),(255,140,30),(255,80,80),(200,60,255),(60,220,255),(50,255,120)]
        cc = colors[min(self._combo-2, len(colors)-1)]
        pulse = 0.9 + 0.1*math.sin(t * 8)

        cx = SCREEN_W - 130; cy = 90
        # Glow background
        gs = pygame.Surface((140,60), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*cc, int(25*pulse)), gs.get_rect(), border_radius=10)
        surf.blit(gs, (cx-10, cy-10))
        # Border
        pygame.draw.rect(surf, (*cc, int(180*pulse)), (cx-10,cy-10,140,60), width=2, border_radius=10)
        # Combo number
        cn = assets.render_text(f"×{self._combo}", "xl", cc, bold=True, shadow=True)
        surf.blit(cn, (cx + 70 - cn.get_width()//2, cy))
        # Label
        cl = assets.render_text("COMBO", "xs", cc)
        surf.blit(cl, (cx + 70 - cl.get_width()//2, cy - 14))

    def _draw_transition(self):
        """Màn đen fade in/out khi chuyển robot."""
        FADE_OUT = 0.8
        FADE_IN  = 0.7

        if self._transition_phase == "out":
            progress = min(1.0, self._transition_t / FADE_OUT)
        else:  # "in"
            progress = max(0.0, 1.0 - self._transition_t / FADE_IN)

        a = int(progress * 255)
        if a <= 0:
            return

        fade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fade.fill((0, 0, 0, a))
        self.screen.blit(fade, (0, 0))

        # Khi gần đen hoàn toàn: hiện tên robot sắp xuất hiện
        if self._transition_phase == "out" and progress > 0.75:
            next_idx = self._get_robot_idx(self._wave_index)
            from src.robot_renderer import ROBOT_PALETTES
            pal = ROBOT_PALETTES[next_idx]
            text_a = int((progress - 0.75) / 0.25 * 255)

            # Dòng tiêu đề
            name_s = assets.render_text(f"ENEMY #{self._wave_index + 1}", "md",
                                         pal["neon"], bold=True)
            name_s.set_alpha(text_a)
            self.screen.blit(name_s,
                (SCREEN_W // 2 - name_s.get_width() // 2, SCREEN_H // 2 - 48))

            title_s = assets.render_text(pal["name"], "xl", pal["neon"], bold=True)
            title_s.set_alpha(text_a)
            self.screen.blit(title_s,
                (SCREEN_W // 2 - title_s.get_width() // 2, SCREEN_H // 2 - 12))

            subtitle_s = assets.render_text(pal["title"], "sm",
                                             (200, 210, 240), shadow=True)
            subtitle_s.set_alpha(text_a)
            self.screen.blit(subtitle_s,
                (SCREEN_W // 2 - subtitle_s.get_width() // 2, SCREEN_H // 2 + 44))

    def _draw_robot_banner(self):
        """Banner tên robot hiện tại ở đầu màn hình (fade out sau 3s)."""
        # Chỉ hiện trong 3s đầu, fade out trong 0.5s cuối
        t    = self._robot_banner_t
        if t <= 0:
            return
        a_f  = min(1.0, t / 0.5) if t < 0.5 else 1.0

        from src.robot_renderer import ROBOT_PALETTES
        pal = self._robot.palette

        cycle = self._wave_index // 7
        wave_num = self._wave_index + 1

        # Nền banner
        bh = 70
        banner = pygame.Surface((SCREEN_W, bh), pygame.SRCALPHA)
        banner.fill((0, 0, 0, int(160 * a_f)))
        self.screen.blit(banner, (0, SCREEN_H // 2 - bh // 2 - 80))

        y0 = SCREEN_H // 2 - bh // 2 - 80 + 8

        # "ENEMY #N" nhỏ
        lbl = assets.render_text(
            f"ENEMY #{wave_num}" + (f"  [ROUND {cycle+1}]" if cycle > 0 else ""),
            "sm", (160, 170, 200))
        lbl.set_alpha(int(200 * a_f))
        self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, y0))

        # Tên robot to + màu neon
        name_s = assets.render_text(pal["name"], "lg", pal["neon"], bold=True,
                                     shadow=True, shadow_color=(0, 0, 0))
        name_s.set_alpha(int(255 * a_f))
        self.screen.blit(name_s,
            (SCREEN_W // 2 - name_s.get_width() // 2, y0 + 26))

        # Thanh neon hai bên tên
        nw = name_s.get_width() + 60
        nx = SCREEN_W // 2 - nw // 2
        ny = y0 + 26 + name_s.get_height() + 4
        pygame.draw.line(self.screen, (*pal["neon"], int(180 * a_f)),
            (nx, ny), (SCREEN_W // 2 - 8, ny), 2)
        pygame.draw.line(self.screen, (*pal["neon"], int(180 * a_f)),
            (SCREEN_W // 2 + 8, ny), (nx + nw, ny), 2)

    # ─── Environment ──────────────────────────────────────────

    def _draw_environment(self, surf):
        """Vẽ môi trường theo map hiện tại."""
        m = self._current_map
        if   m == 0: self._draw_env_lab(surf)
        elif m == 1: self._draw_env_space(surf)
        elif m == 2: self._draw_env_jungle(surf)
        else:        self._draw_env_lab(surf)

    # ─── MAP 0: LAB (Phòng thí nghiệm — xanh acid) ───────────

    def _draw_env_lab(self, surf):
        hz = SCREEN_H // 2
        CEI = (8, 12, 22); HOR = (18, 28, 50); FLR = (10, 18, 32)
        NEON = (0, 180, 80); GRID = (18, 35, 22)

        for y in range(hz+1):
            t = y/hz
            pygame.draw.line(surf, (
                int(CEI[0]+(HOR[0]-CEI[0])*t),
                int(CEI[1]+(HOR[1]-CEI[1])*t),
                int(CEI[2]+(HOR[2]-CEI[2])*t),
            ), (0,y),(SCREEN_W,y))
        for y in range(SCREEN_H-hz):
            t = y/(SCREEN_H-hz)
            pygame.draw.line(surf, (
                int(HOR[0]+(FLR[0]-HOR[0])*t),
                int(HOR[1]+(FLR[1]-HOR[1])*t),
                int(HOR[2]+(FLR[2]-HOR[2])*t),
            ), (0,hz+y),(SCREEN_W,hz+y))

        # Lưới sàn xanh acid
        vp_x = SCREEN_W//2
        for i in range(1,15):
            t = (i/14)**1.6; y = int(hz+(SCREEN_H-hz)*t)
            c = NEON if i%3==0 else GRID
            w = 2 if i%3==0 else 1
            pygame.draw.line(surf, c, (0,y),(SCREEN_W,y),w)
        for i in range(21):
            angle = (i/20-0.5)*1.8
            ex = vp_x+int(math.tan(angle)*(SCREEN_H-hz)*1.1)
            c = NEON if i%4==0 else GRID
            pygame.draw.line(surf, c, (vp_x,hz),(ex,SCREEN_H),2 if i%4==0 else 1)

        # Ống nghiệm và thiết bị lab trên tường hai bên
        for side_x in [0, SCREEN_W-70]:
            pygame.draw.rect(surf, (12,18,30),(side_x,0,70,SCREEN_H))
            ex = side_x+(69 if side_x>0 else 0)
            pygame.draw.line(surf, NEON,(ex,0),(ex,SCREEN_H),2)
            for i in range(4):
                ty = 80+i*110
                # Ống nghiệm
                tw = 20; th = 55; tx = side_x+(25 if side_x==0 else 25)
                pygame.draw.rect(surf,(15,25,40),(tx,ty,tw,th),border_radius=8)
                # Chất lỏng màu
                colors_tube = [(0,220,100),(100,255,180),(0,180,60),(180,255,80)]
                liq_h = int(th*0.6); liq_c = colors_tube[i%4]
                liq_pulse = 0.7+0.3*math.sin(self._time*2+i)
                liq_c = tuple(min(255,int(c2*liq_pulse)) for c2 in liq_c)
                pygame.draw.rect(surf,liq_c,(tx+2,ty+th-liq_h+2,tw-4,liq_h-4),border_radius=6)
                pygame.draw.rect(surf,NEON,(tx,ty,tw,th),width=1,border_radius=8)
                # Bubble animation
                bub_y = ty+th-liq_h+int((self._time*30+i*20)%(liq_h))
                pygame.draw.circle(surf,(200,255,220),(tx+tw//2,bub_y),2)
        self._draw_wall_lights_env(surf, hz)
        self._draw_fog(surf, hz)

    # ─── MAP 1: SPACE STATION (Trạm vũ trụ — xanh thiên hà) ─────

    def _draw_env_space(self, surf):
        hz = SCREEN_H // 2
        surf.fill((4, 6, 16))

        # Sao nền
        import random as rnd
        rng = rnd.Random(99)
        for _ in range(120):
            sx = rng.randint(0, SCREEN_W); sy = rng.randint(0, SCREEN_H)
            sr = rng.randint(1,2)
            a = int(rng.randint(40,180)*(0.7+0.3*math.sin(self._time*0.5+sx*0.02)))
            ss = pygame.Surface((sr*2,sr*2),pygame.SRCALPHA)
            pygame.draw.circle(ss,(180,200,255,a),(sr,sr),sr)
            surf.blit(ss,(sx,sy))

        # Nebula cloud background
        for ni in range(3):
            nx = SCREEN_W//4*(ni+1); ny = SCREEN_H//3
            nr = 80+ni*30
            na = int(15+ni*8)
            ns = pygame.Surface((nr*2,nr*2),pygame.SRCALPHA)
            nc_list = [(80,40,120),(40,60,140),(120,60,180)]
            pygame.draw.circle(ns,(*nc_list[ni],na),(nr,nr),nr)
            surf.blit(ns,(nx-nr,ny-nr))

        # Horizon line (planet curvature effect)
        pygame.draw.line(surf,(20,40,80),(0,hz),(SCREEN_W,hz),1)

        # Sàn kim loại không gian
        for y in range(SCREEN_H-hz):
            t = y/(SCREEN_H-hz)
            c = (int(8+t*8),int(10+t*12),int(22+t*18))
            pygame.draw.line(surf,c,(0,hz+y),(SCREEN_W,hz+y))

        vp_x = SCREEN_W//2
        NEON=(40,100,255); GRID=(20,35,70)
        for i in range(1,15):
            t=(i/14)**1.6; y=int(hz+(SCREEN_H-hz)*t)
            c=NEON if i%3==0 else GRID
            pygame.draw.line(surf,c,(0,y),(SCREEN_W,y),2 if i%3==0 else 1)
        for i in range(21):
            angle=(i/20-0.5)*1.8
            ex=vp_x+int(math.tan(angle)*(SCREEN_H-hz)*1.1)
            c=NEON if i%4==0 else GRID
            pygame.draw.line(surf,c,(vp_x,hz),(ex,SCREEN_H),2 if i%4==0 else 1)

        # Cột trụ không gian hai bên
        for side_x in [0, SCREEN_W-70]:
            pygame.draw.rect(surf,(6,10,28),(side_x,0,70,SCREEN_H))
            ex=side_x+(69 if side_x>0 else 0)
            pygame.draw.line(surf,(40,100,255),(ex,0),(ex,SCREEN_H),2)
            for i in range(5):
                py=60+i*90; bx=side_x+8
                pygame.draw.rect(surf,(10,18,50),(bx,py,54,55),border_radius=4)
                # Hologram display
                holo_c=(40,100,200) if math.sin(self._time*1.5+i)>0 else (20,60,150)
                pygame.draw.rect(surf,holo_c,(bx+4,py+4,46,30),border_radius=3)
                for li in range(3):
                    lw=int(20+math.sin(self._time+li)*10)
                    pygame.draw.line(surf,(80,160,255),(bx+8,py+12+li*7),(bx+8+lw,py+12+li*7),1)
                pygame.draw.circle(surf,(255,100,40),(bx+10,py+45),3)
        self._draw_fog(surf, hz)

    # ─── MAP 2: JUNGLE BASE (Rừng neon — xanh lá nhiệt đới) ─────

    def _draw_env_jungle(self, surf):
        hz = SCREEN_H // 2
        CEI=(6,15,8); HOR=(14,30,18); FLR=(8,20,10)
        NEON=(20,200,60); GRID=(15,40,18)

        for y in range(hz+1):
            t=y/hz
            pygame.draw.line(surf,(
                int(CEI[0]+(HOR[0]-CEI[0])*t),
                int(CEI[1]+(HOR[1]-CEI[1])*t),
                int(CEI[2]+(HOR[2]-CEI[2])*t),
            ),(0,y),(SCREEN_W,y))
        for y in range(SCREEN_H-hz):
            t=y/(SCREEN_H-hz)
            pygame.draw.line(surf,(
                int(HOR[0]+(FLR[0]-HOR[0])*t),
                int(HOR[1]+(FLR[1]-HOR[1])*t),
                int(HOR[2]+(FLR[2]-HOR[2])*t),
            ),(0,hz+y),(SCREEN_W,hz+y))

        vp_x=SCREEN_W//2
        for i in range(1,15):
            t=(i/14)**1.6; y=int(hz+(SCREEN_H-hz)*t)
            c=NEON if i%3==0 else GRID
            pygame.draw.line(surf,c,(0,y),(SCREEN_W,y),2 if i%3==0 else 1)
        for i in range(21):
            angle=(i/20-0.5)*1.8
            ex=vp_x+int(math.tan(angle)*(SCREEN_H-hz)*1.1)
            c=NEON if i%4==0 else GRID
            pygame.draw.line(surf,c,(vp_x,hz),(ex,SCREEN_H),2 if i%4==0 else 1)

        # Cây neon hai bên
        for side_x in [0, SCREEN_W-70]:
            pygame.draw.rect(surf,(8,18,10),(side_x,0,70,SCREEN_H))
            ex=side_x+(69 if side_x>0 else 0)
            pygame.draw.line(surf,NEON,(ex,0),(ex,SCREEN_H),2)
            for i in range(4):
                ty=50+i*115; tx=side_x+(5 if side_x==0 else 5)
                # Thân cây
                pygame.draw.rect(surf,(25,45,20),(tx+20,ty,14,70))
                # Tán lá neon
                for li in range(3):
                    lx2=tx+10+li*8; ly2=ty+li*20
                    lw=55-li*12; lh=28-li*5
                    ls=pygame.Surface((lw,lh),pygame.SRCALPHA)
                    leaf_a=int(80*(0.7+0.3*math.sin(self._time*1.2+i+li)))
                    leaf_c=(20,200,60) if li==0 else ((30,160,50) if li==1 else (40,220,80))
                    pygame.draw.ellipse(ls,(*leaf_c,leaf_a),ls.get_rect())
                    surf.blit(ls,(lx2,ly2))
                # Quả phát sáng
                fx=tx+25; fy=ty+55
                fp=abs(math.sin(self._time*2+i))
                fc=(int(30+fp*220),int(180+fp*60),int(20+fp*40))
                pygame.draw.circle(surf,fc,(fx,fy),5)

        # Hơi nước / fog nền xanh
        for fi in range(5):
            fy=hz-20+fi*5; fa=int(30*(1-fi/5))
            fs=pygame.Surface((SCREEN_W,4),pygame.SRCALPHA)
            fs.fill((20,200,60,fa))
            surf.blit(fs,(0,fy))
        self._draw_wall_lights_env(surf, hz)
        self._draw_fog(surf, hz)

    def _draw_floor_grid(self, surf, hz):
        """Lưới sàn neon perspective."""
        vp_x = SCREEN_W // 2
        n_h = 14
        for i in range(1, n_h + 1):
            t    = (i / n_h) ** 1.6
            y    = int(hz + (SCREEN_H - hz) * t)
            is_main = (i % 3 == 0)
            c    = ENV_NEON_LINE if is_main else ENV_GRID_LINE
            pygame.draw.line(surf, c, (0, y), (SCREEN_W, y), 2 if is_main else 1)
        n_v = 20
        for i in range(n_v + 1):
            angle = (i / n_v - 0.5) * 1.8
            ex    = vp_x + int(math.tan(angle) * (SCREEN_H - hz) * 1.1)
            is_main = (i % 4 == 0)
            c     = ENV_NEON_LINE if is_main else ENV_GRID_LINE
            pygame.draw.line(surf, c, (vp_x, hz), (ex, SCREEN_H), 2 if is_main else 1)

    def _draw_ceiling_grid(self, surf, hz):
        """Lưới trần (thêm chiều sâu không gian)."""
        vp_x = SCREEN_W // 2
        n_v  = 12
        for i in range(n_v + 1):
            angle = (i / n_v - 0.5) * 1.6
            ex    = vp_x + int(math.tan(angle) * hz * 1.1)
            c     = (18, 25, 50) if i % 4 != 0 else (25, 40, 80)
            pygame.draw.line(surf, c, (vp_x, hz), (ex, 0))

        n_h = 8
        for i in range(1, n_h + 1):
            t = (i / n_h) ** 1.4
            y = int(hz - hz * t)
            pygame.draw.line(surf, (18, 25, 50), (0, y), (SCREEN_W, y))

    def _draw_wall_lights_env(self, surf, hz):
        """Đèn neon gắn trần + hào quang."""
        for lt in self._wall_lights:
            flicker = 0.75 + 0.25 * math.sin(self._time * 4 + lt["flicker"])
            intensity = lt["intensity"] * flicker
            lx, ly   = lt["x"], lt["y"]
            r, g, b  = lt["color"]

            # Bóng đèn
            pygame.draw.rect(surf, (50, 55, 70), (lx - 6, ly - 4, 12, 8), border_radius=3)
            pygame.draw.rect(surf, (200, 210, 255), (lx - 4, ly, 8, 4), border_radius=2)

            # Vầng sáng côn
            cone_h = int((SCREEN_H // 2 - ly) * 0.85)
            for ci in range(6):
                t    = ci / 6
                cw   = int(20 + t * 120) * intensity
                ca   = int(40 * (1 - t) * intensity)
                cr, cg, cb = r, g, b
                cone_surf = pygame.Surface((int(cw * 2), max(1, int(cone_h * (1 - t + 0.1)))), pygame.SRCALPHA)
                pygame.draw.ellipse(cone_surf, (cr, cg, cb, ca), cone_surf.get_rect())
                surf.blit(cone_surf, (lx - int(cw), ly + int(cone_h * t)))

    def _draw_side_panels(self, surf, hz):
        """Cột/tường hai bên phong cách sci-fi."""
        for side_x, flip in [(0, False), (SCREEN_W - 80, True)]:
            panel_c = (18, 22, 42)
            pygame.draw.rect(surf, panel_c, (side_x, 0, 80, SCREEN_H))
            # Đường viền neon
            edge_x  = side_x + (79 if flip else 0)
            pygame.draw.line(surf, (0, 80, 180), (edge_x, 0), (edge_x, SCREEN_H), 2)
            # Các nút/panel nhỏ
            for i in range(6):
                py = 80 + i * 90
                bx = side_x + (10 if not flip else 15)
                bc = (30, 40, 70)
                pygame.draw.rect(surf, bc, (bx, py, 55, 60), border_radius=5)
                # Đèn nhỏ nhấp nháy
                blink_c = (0, 200, 80) if math.sin(self._time * 2 + i) > 0 else (0, 60, 30)
                pygame.draw.circle(surf, blink_c, (bx + 8, py + 10), 4)
                # Đường kẻ dữ liệu giả
                for li in range(3):
                    lw = random.choice([15, 25, 35])
                    pygame.draw.line(surf, (40, 60, 100),
                        (bx + 16, py + 22 + li * 10),
                        (bx + 16 + lw, py + 22 + li * 10), 1)

    def _draw_fog(self, surf, hz):
        """Sương mù xa để che chân trời."""
        fog_h = 60
        for y in range(fog_h):
            a = int(100 * (1 - y / fog_h))
            fog_surf = pygame.Surface((SCREEN_W, 1), pygame.SRCALPHA)
            fog_surf.fill((*ENV_FOG, a))
            surf.blit(fog_surf, (0, hz - fog_h // 2 + y))

    # ─── GUN (cinematic) ──────────────────────────────────────

    def _draw_gun(self, surf):
        t  = self._time
        rc = self._gun_recoil

        # Vị trí base của súng (góc dưới phải màn hình)
        gx = SCREEN_W - 290 + int(self._gun_sway_x * 6)
        gy = SCREEN_H - 240 + int(rc * 55) + int(self._gun_sway_y * 4)

        # ----- TAY -----
        self._draw_hand_arm(surf, gx, gy)

        # ----- THÂN SÚNG -----
        self._draw_gun_body(surf, gx, gy, rc)

        # ----- MUZZLE FLASH -----
        if self._muzzle_t > 0.05:
            self._draw_muzzle_flash_gun(surf, gx, gy)

    def _draw_hand_arm(self, surf, gx, gy):
        """Tay cầm sung."""
        skin = (110, 85, 65)
        skin_d = (85, 65, 50)

        # Cánh tay
        arm_pts = [
            (gx + 90, gy + 210),
            (gx + 160, gy + 260),
            (gx + 180, gy + 290),
            (gx + 120, gy + 290),
            (gx + 60,  gy + 220),
        ]
        pygame.draw.polygon(surf, skin_d, arm_pts)
        pygame.draw.polygon(surf, (70, 52, 40), arm_pts, 1)

        # Bàn tay
        hand_pts = [
            (gx + 46,  gy + 130),
            (gx + 110, gy + 110),
            (gx + 130, gy + 155),
            (gx + 115, gy + 200),
            (gx + 50,  gy + 215),
            (gx + 30,  gy + 170),
        ]
        pygame.draw.polygon(surf, skin, hand_pts)
        pygame.draw.polygon(surf, skin_d, hand_pts, 2)

        # Ngón tay quanh cò
        finger_pts = [(gx + 70, gy + 165), (gx + 100, gy + 155),
                      (gx + 105, gy + 185), (gx + 72,  gy + 195)]
        pygame.draw.polygon(surf, skin, finger_pts)
        # Đường khớp ngón
        pygame.draw.line(surf, skin_d, (gx + 75, gy + 168), (gx + 98, gy + 160), 1)

    def _draw_gun_body(self, surf, gx, gy, rc):
        """Súng cơ giới siêu cinematic."""
        dark    = (22,  24,  34)
        mid     = (48,  54,  74)
        light   = (85,  96,  126)
        accent  = (0,   190, 255)
        chrome  = (145, 155, 178)
        orange  = (220, 110, 30)
        scratch = (62,  68,  88)

        t = self._time
        rc_pulse = 1.0 - rc * 0.3   # scale khi recoil

        # ─── LASER SIGHT BEAM (trước mọi thứ) ───
        laser_x = gx - 76
        laser_y = gy + 103
        if self._aim_on_robot:
            lc = (255, 50, 50)
        else:
            lc = (255, 80, 80)
        # Tia laser
        for lw, la in [(6, 8), (3, 20), (1, 60)]:
            ls = pygame.Surface((200, lw), pygame.SRCALPHA)
            ls.fill((*lc, la))
            surf.blit(ls, (laser_x - 200, laser_y - lw // 2))
        # Dot laser trên robot
        if self._aim_on_robot:
            mx, my = pygame.mouse.get_pos()
            dot_a = int(200 * (0.7 + 0.3 * math.sin(t * 12)))
            for dr, da in [(8, 30), (4, 80), (2, 200)]:
                ds = pygame.Surface((dr * 2, dr * 2), pygame.SRCALPHA)
                pygame.draw.circle(ds, (255, 50, 50, min(255, int(da * dot_a / 200))), (dr, dr), dr)
                surf.blit(ds, (mx - dr, my - dr))

        # ─── HEAT HAZE sau bắn (distortion effect) ───
        if self._muzzle_t > 0.3:
            haze_x = gx - 96
            haze_y = gy + 50
            for hi in range(4):
                ha = int(self._muzzle_t * (25 - hi * 5))
                if ha > 2:
                    hs = pygame.Surface((30 + hi * 10, 60 + hi * 15), pygame.SRCALPHA)
                    hs.fill((200, 220, 255, ha))
                    surf.blit(hs, (haze_x - 20 - hi * 5, haze_y - 20 - hi * 8))

        # ─── Barrel + Handguard ───
        barrel_x = gx - 100
        barrel_y = gy + 72

        # Handguard với ambient occlusion
        pts_hg = [
            (barrel_x,       barrel_y - 10),
            (barrel_x + 90,  barrel_y - 14),
            (barrel_x + 90,  barrel_y + 22),
            (barrel_x,       barrel_y + 18),
        ]
        pygame.draw.polygon(surf, mid, pts_hg)
        # AO shadow trên handguard
        ao_s = pygame.Surface((92, 6), pygame.SRCALPHA)
        ao_s.fill((0, 0, 0, 40))
        surf.blit(ao_s, (barrel_x, barrel_y + 16))
        pygame.draw.polygon(surf, light, pts_hg, 2)

        # Khe thoát nhiệt — neon glow khi bắn nhiều
        heat_glow = min(1.0, self._muzzle_t * 0.8 + rc * 0.4)
        for i in range(6):
            hx2 = barrel_x + 6 + i * 14
            pygame.draw.rect(surf, dark, (hx2, barrel_y - 8, 9, 7), border_radius=1)
            if heat_glow > 0.1:
                ha = int(heat_glow * 120)
                hs = pygame.Surface((9, 7), pygame.SRCALPHA)
                hs.fill((255, 120, 30, ha))
                surf.blit(hs, (hx2, barrel_y - 8))

        # Nòng chính
        pygame.draw.rect(surf, dark, (gx - 80, gy + 82, 80, 14), border_radius=3)
        pygame.draw.rect(surf, chrome, (gx - 80, gy + 82, 80, 5))
        pygame.draw.line(surf, (38, 42, 58), (gx - 78, gy + 89), (gx - 4, gy + 89), 2)

        # Đầu nòng với crown cut
        pygame.draw.rect(surf, dark, (gx - 98, gy + 77, 20, 24), border_radius=3)
        pygame.draw.ellipse(surf, (8, 10, 16), (gx - 96, gy + 79, 14, 20))
        pygame.draw.rect(surf, chrome, (gx - 98, gy + 77, 20, 24), width=2, border_radius=3)
        # Brake slots trên đầu nòng
        for bi in range(3):
            pygame.draw.rect(surf, (60, 65, 80), (gx - 96, gy + 80 + bi * 6, 14, 2))

        # ─── Receiver ───
        rec_pts = [
            (gx,        gy + 60),
            (gx + 132,  gy + 49),
            (gx + 140,  gy + 132),
            (gx + 10,   gy + 142),
        ]
        pygame.draw.polygon(surf, mid, rec_pts)
        pygame.draw.polygon(surf, light, rec_pts, 2)
        pygame.draw.line(surf, chrome, (gx, gy + 60), (gx + 132, gy + 49), 2)

        # Xước / wear marks trên receiver
        for i in range(5):
            sx1 = gx + 15 + i * 20
            sy1 = gy + 70 + i * 3
            pygame.draw.line(surf, scratch, (sx1, sy1), (sx1 + 8, sy1 - 2), 1)

        # Panel chi tiết
        for i in range(3):
            px2 = gx + 18 + i * 36
            pygame.draw.rect(surf, dark, (px2, gy + 67, 28, 15), border_radius=2)
            pygame.draw.line(surf, (60, 70, 100), (px2 + 4, gy + 74), (px2 + 22, gy + 74), 1)
            # Indicator light
            li_c = accent if i == 0 else (dark[0], dark[1], dark[2])
            pygame.draw.circle(surf, li_c, (px2 + 24, gy + 70), 3)

        # ─── Rail + Scope CINEMATIC ───
        rail_y = gy + 49
        pygame.draw.rect(surf, dark, (gx + 8, rail_y - 9, 116, 11), border_radius=2)
        for i in range(9):
            rx2 = gx + 12 + i * 12
            pygame.draw.rect(surf, (36, 40, 56), (rx2, rail_y - 7, 9, 7), border_radius=1)

        # Scope body
        sc_x, sc_y = gx + 28, rail_y - 26
        sc_w, sc_h = 78, 20
        pygame.draw.rect(surf, dark, (sc_x, sc_y, sc_w, sc_h), border_radius=6)
        pygame.draw.rect(surf, chrome, (sc_x, sc_y, sc_w, sc_h), width=1, border_radius=6)

        # Scope lens glow
        scope_glow = 0.5 + 0.5 * math.sin(t * 2.3)
        # Kính trước
        pygame.draw.ellipse(surf, (0, 15, 35), (sc_x + 2, sc_y + 3, 14, 14))
        pygame.draw.ellipse(surf, (0, int(60 + 40*scope_glow), int(140 + 60*scope_glow)),
                            (sc_x + 4, sc_y + 5, 10, 10))
        pygame.draw.circle(surf, (int(100*scope_glow), int(200*scope_glow), 255),
                           (sc_x + 9, sc_y + 10), 2)
        # Kính sau
        pygame.draw.ellipse(surf, (0, 15, 35), (sc_x + sc_w - 16, sc_y + 3, 14, 14))
        pygame.draw.ellipse(surf, (0, int(40+30*scope_glow), int(100+50*scope_glow)),
                            (sc_x + sc_w - 14, sc_y + 5, 10, 10))
        # Scope glow hào quang
        sg_a = int(scope_glow * 35)
        sg_s = pygame.Surface((sc_w + 20, sc_h + 20), pygame.SRCALPHA)
        pygame.draw.rect(sg_s, (0, 180, 255, sg_a), sg_s.get_rect(), border_radius=8)
        surf.blit(sg_s, (sc_x - 10, sc_y - 10))

        # Crosshair reticle trong scope (nhỏ)
        rle_x, rle_y = sc_x + 9, sc_y + 10
        pygame.draw.line(surf, (0, 200, 255), (rle_x - 4, rle_y), (rle_x - 1, rle_y), 1)
        pygame.draw.line(surf, (0, 200, 255), (rle_x + 1, rle_y), (rle_x + 4, rle_y), 1)
        pygame.draw.line(surf, (0, 200, 255), (rle_x, rle_y - 4), (rle_x, rle_y - 1), 1)
        pygame.draw.line(surf, (0, 200, 255), (rle_x, rle_y + 1), (rle_x, rle_y + 4), 1)

        # Turret knob scope
        pygame.draw.rect(surf, chrome, (sc_x + 32, sc_y - 8, 14, 10), border_radius=2)
        pygame.draw.line(surf, dark, (sc_x + 39, sc_y - 6), (sc_x + 39, sc_y - 2), 1)

        # ─── Magazine ───
        mag_pts = [
            (gx + 50,  gy + 140),
            (gx + 80,  gy + 135),
            (gx + 88,  gy + 204),
            (gx + 55,  gy + 212),
        ]
        pygame.draw.polygon(surf, dark, mag_pts)
        # Indicator strip
        mag_strip_s = pygame.Surface((24, 6), pygame.SRCALPHA)
        mag_strip_s.fill((0, 200, 80, 120))
        surf.blit(mag_strip_s, (gx + 54, gy + 165))
        pygame.draw.polygon(surf, mid, mag_pts, 2)
        for i in range(4):
            my3 = gy + 148 + i * 14
            pygame.draw.line(surf, mid, (gx + 53, my3), (gx + 84, my3 - 2), 1)

        # ─── Pistol grip ───
        grip_pts = [
            (gx + 80,  gy + 136),
            (gx + 120, gy + 128),
            (gx + 138, gy + 234),
            (gx + 96,  gy + 244),
        ]
        pygame.draw.polygon(surf, dark, grip_pts)
        # Grip checkering texture
        for i in range(6):
            for j in range(3):
                gx2 = gx + 86 + j * 12
                gy2 = gy + 146 + i * 14
                pygame.draw.circle(surf, (34, 38, 54), (gx2, gy2), 2)
                pygame.draw.circle(surf, (50, 56, 76), (gx2, gy2), 1)
        pygame.draw.polygon(surf, mid, grip_pts, 2)

        # ─── Trigger guard ───
        tg = pygame.Rect(gx + 54, gy + 138, 58, 44)
        pygame.draw.arc(surf, mid, tg, math.pi * 0.08, math.pi * 0.92, 3)
        # Trigger
        pygame.draw.rect(surf, chrome, (gx + 71, gy + 151, 9, 24), border_radius=3)
        pygame.draw.line(surf, (100, 110, 140), (gx + 73, gy + 153), (gx + 73, gy + 173), 1)

        # ─── Charging handle ───
        pygame.draw.rect(surf, mid, (gx + 116, gy + 66, 24, 12), border_radius=3)
        pygame.draw.rect(surf, chrome, (gx + 116, gy + 66, 24, 12), width=1, border_radius=3)
        pygame.draw.rect(surf, dark, (gx + 118, gy + 70, 20, 5), border_radius=1)

        # ─── Selector / Accent stripe ───
        pygame.draw.line(surf, accent, (gx + 4, gy + 100), (gx + 126, gy + 91), 2)
        # Selector LED
        sel_c = (255, 80, 80) if rc > 0.5 else accent
        pygame.draw.circle(surf, sel_c, (gx + 122, gy + 94), 5)
        pygame.draw.circle(surf, dark, (gx + 122, gy + 94), 3)
        # Glow trên selector
        sel_gs = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(sel_gs, (*sel_c, 60), (10, 10), 10)
        surf.blit(sel_gs, (gx + 112, gy + 84))

        # ─── Stock ───
        stock_pts = [
            (gx + 130, gy + 51),
            (gx + 163, gy + 44),
            (gx + 178, gy + 113),
            (gx + 148, gy + 130),
            (gx + 126, gy + 134),
        ]
        pygame.draw.polygon(surf, mid, stock_pts)
        # Stock cheek weld
        pygame.draw.rect(surf, (38, 44, 62), (gx + 136, gy + 55, 28, 50), border_radius=4)
        pygame.draw.polygon(surf, light, stock_pts, 2)
        # Butt pad
        pygame.draw.rect(surf, dark, (gx + 164, gy + 46, 16, 66), border_radius=5)
        pygame.draw.rect(surf, (60, 65, 80), (gx + 164, gy + 46, 16, 66), width=1, border_radius=5)
        # Rubber texture stripes
        for i in range(4):
            pygame.draw.line(surf, (45, 50, 65),
                (gx + 166, gy + 54 + i * 14), (gx + 178, gy + 54 + i * 14), 1)

        # ─── Underslung Flashlight / Foregrip ───
        pygame.draw.rect(surf, dark, (gx - 78, gy + 95, 60, 16), border_radius=4)
        pygame.draw.rect(surf, mid, (gx - 78, gy + 95, 60, 16), width=1, border_radius=4)
        # Flashlight head
        pygame.draw.circle(surf, (80, 85, 100), (gx - 79, gy + 103), 8)
        lens_a = int(180 + 75 * math.sin(t * 1.5))
        pygame.draw.circle(surf, (orange[0], orange[1], 50), (gx - 79, gy + 103), 5)
        pygame.draw.circle(surf, (255, 230, 180), (gx - 79, gy + 103), 2)
        # Flashlight cone (khi bắn)
        if self._muzzle_t < 0.1:
            fl_s = pygame.Surface((120, 40), pygame.SRCALPHA)
            pygame.draw.polygon(fl_s, (255, 200, 100, 18),
                [(0, 20), (120, 0), (120, 40)])
            surf.blit(fl_s, (gx - 200, gy + 83))

        # ─── Ambient glow dưới súng ───
        gun_gs = pygame.Surface((240, 30), pygame.SRCALPHA)
        gga = int(20 + 15 * math.sin(t * 1.8))
        pygame.draw.ellipse(gun_gs, (0, 140, 255, gga), gun_gs.get_rect())
        surf.blit(gun_gs, (gx - 110, gy + 150))

        # ─── Barrel (nòng súng) ───
        barrel_x = gx - 100
        barrel_y = gy + 72

        # Bọc nòng (handguard)
        pts_hg = [
            (barrel_x,       barrel_y - 10),
            (barrel_x + 90,  barrel_y - 14),
            (barrel_x + 90,  barrel_y + 22),
            (barrel_x,       barrel_y + 18),
        ]
        pygame.draw.polygon(surf, mid, pts_hg)
        pygame.draw.polygon(surf, light, pts_hg, 2)

        # Khe thoát nhiệt trên nòng
        for i in range(5):
            hx = barrel_x + 8 + i * 16
            pygame.draw.rect(surf, dark, (hx, barrel_y - 8, 8, 6), border_radius=1)

        # Đường rãnh nòng
        pygame.draw.line(surf, dark, (barrel_x + 2, barrel_y + 4),
                         (barrel_x + 88, barrel_y + 4), 2)

        # Ống phóng chính (nòng thực sự)
        for i, (dx, dy, dw, dh) in enumerate([
            (-80, 82, 80, 14),   # nòng chính
            (-80, 82, 80, 6),    # viền trên
        ]):
            c = dark if i == 0 else chrome
            pygame.draw.rect(surf, c, (gx + dx, gy + dy, dw, dh),
                             border_radius=3 if i == 0 else 0)
        # Đầu nòng
        pygame.draw.rect(surf, dark, (gx - 96, gy + 78, 18, 22), border_radius=2)
        pygame.draw.ellipse(surf, (15, 15, 20), (gx - 94, gy + 80, 12, 18))  # lỗ nòng
        # Viền nòng chrome
        pygame.draw.rect(surf, chrome, (gx - 96, gy + 78, 18, 22), width=1, border_radius=2)

        # ─── Receiver (khung chính) ───
        rec_pts = [
            (gx,        gy + 60),
            (gx + 130,  gy + 50),
            (gx + 138,  gy + 130),
            (gx + 10,   gy + 140),
        ]
        pygame.draw.polygon(surf, mid, rec_pts)

        # Viền receiver trên sáng
        pygame.draw.polygon(surf, light, rec_pts, 2)
        pygame.draw.line(surf, chrome,
            (gx, gy + 60), (gx + 130, gy + 50), 2)

        # Chi tiết panel trên receiver
        for i in range(3):
            px = gx + 20 + i * 36
            pygame.draw.rect(surf, dark, (px, gy + 68, 28, 14), border_radius=2)
            pygame.draw.line(surf, (60, 70, 100),
                (px + 4, gy + 73), (px + 22, gy + 73), 1)

        # ─── Scope / Rail ───
        rail_y = gy + 50
        pygame.draw.rect(surf, dark, (gx + 10, rail_y - 8, 110, 10), border_radius=2)
        # Picatinny rail (khe)
        for i in range(8):
            rx = gx + 14 + i * 13
            pygame.draw.rect(surf, (38, 42, 58), (rx, rail_y - 6, 9, 6), border_radius=1)

        # Scope thân
        pygame.draw.rect(surf, dark, (gx + 30, rail_y - 24, 70, 18), border_radius=5)
        pygame.draw.rect(surf, chrome, (gx + 30, rail_y - 24, 70, 18), width=1, border_radius=5)
        # Thấu kính scope
        pygame.draw.ellipse(surf, (0, 20, 40), (gx + 32, rail_y - 22, 14, 14))
        pygame.draw.ellipse(surf, (0, 80, 160), (gx + 34, rail_y - 20, 10, 10))
        pygame.draw.circle(surf, (0, 200, 255), (gx + 39, rail_y - 15), 2)
        # Kính sau scope
        pygame.draw.ellipse(surf, (0, 20, 40), (gx + 82, rail_y - 22, 14, 14))
        pygame.draw.ellipse(surf, (0, 60, 120), (gx + 84, rail_y - 20, 10, 10))
        # Núm chỉnh scope
        pygame.draw.rect(surf, chrome, (gx + 60, rail_y - 28, 12, 8), border_radius=2)

        # ─── Magazine ───
        mag_pts = [
            (gx + 50,  gy + 138),
            (gx + 80,  gy + 133),
            (gx + 88,  gy + 200),
            (gx + 55,  gy + 208),
        ]
        pygame.draw.polygon(surf, dark, mag_pts)
        pygame.draw.polygon(surf, mid, mag_pts, 2)
        # Gân magazine
        for i in range(3):
            my2 = gy + 150 + i * 18
            pygame.draw.line(surf, mid, (gx + 52, my2), (gx + 84, my2 - 2), 1)

        # ─── Pistol grip ───
        grip_pts = [
            (gx + 80,  gy + 135),
            (gx + 118, gy + 128),
            (gx + 135, gy + 230),
            (gx + 95,  gy + 240),
        ]
        pygame.draw.polygon(surf, dark, grip_pts)
        # Texture grip
        for i in range(5):
            for j in range(3):
                grdx = gx + 84 + j * 12
                grdy = gy + 148 + i * 16
                pygame.draw.circle(surf, (38, 42, 58), (grdx, grdy), 2)
        pygame.draw.polygon(surf, mid, grip_pts, 2)

        # ─── Trigger guard ───
        tg_rect = pygame.Rect(gx + 55, gy + 138, 55, 42)
        pygame.draw.arc(surf, mid, tg_rect, math.pi * 0.1, math.pi * 0.9, 3)

        # Cò súng
        pygame.draw.rect(surf, chrome, (gx + 72, gy + 152, 8, 22), border_radius=3)

        # ─── Charging handle ───
        pygame.draw.rect(surf, chrome, (gx + 118, gy + 68, 20, 10), border_radius=2)
        pygame.draw.rect(surf, dark,   (gx + 120, gy + 72, 16, 4),  border_radius=1)

        # ─── Accent stripe / selector ───
        pygame.draw.line(surf, accent,
            (gx + 5, gy + 100), (gx + 125, gy + 92), 2)
        pygame.draw.circle(surf, accent, (gx + 120, gy + 95), 4)
        pygame.draw.circle(surf, dark,   (gx + 120, gy + 95), 2)

        # ─── Stock ───
        stock_pts = [
            (gx + 128, gy + 52),
            (gx + 160, gy + 46),
            (gx + 175, gy + 112),
            (gx + 145, gy + 128),
            (gx + 125, gy + 132),
        ]
        pygame.draw.polygon(surf, mid, stock_pts)
        pygame.draw.polygon(surf, light, stock_pts, 2)
        # Butt pad
        pygame.draw.rect(surf, dark, (gx + 162, gy + 48, 14, 62), border_radius=4)
        pygame.draw.rect(surf, chrome, (gx + 162, gy + 48, 14, 62), width=1, border_radius=4)

        # ─── Flashlight rail dưới nòng ───
        pygame.draw.rect(surf, dark, (gx - 75, gy + 96, 55, 14), border_radius=3)
        pygame.draw.circle(surf, orange, (gx - 76, gy + 103), 6)
        pygame.draw.circle(surf, (255, 220, 150), (gx - 76, gy + 103), 3)

    def _draw_muzzle_flash_gun(self, surf, gx, gy):
        t   = self._muzzle_t
        mx  = gx - 96
        my  = gy + 89   # đầu nòng

        # Lõi sáng
        for r, c, a in [
            (22, (255, 255, 220), int(t * 230)),
            (36, (255, 200, 80),  int(t * 160)),
            (52, (255, 140, 30),  int(t * 90)),
            (72, (255, 80,  0),   int(t * 45)),
        ]:
            gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*c, a), (r, r), r)
            surf.blit(gs, (mx - r, my - r))

        # Tia lửa xung quanh
        for i in range(8):
            ang  = i * math.pi / 4 + self._time * 8
            tx   = mx + math.cos(ang) * (30 + random.randint(-8, 8))
            ty   = my + math.sin(ang) * (20 + random.randint(-5, 5))
            a    = int(t * random.randint(120, 220))
            r    = random.randint(2, 5)
            pygame.draw.circle(surf, (255, 220, 80), (int(tx), int(ty)), r)

        # Khói
        smoke_c = int(t * 40)
        for i in range(3):
            sr = 15 + i * 10
            sx = mx - 20 - i * 15 + random.randint(-4, 4)
            sy = my - i * 8 + random.randint(-4, 4)
            ss = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ss, (80, 85, 95, smoke_c), (sr, sr), sr)
            surf.blit(ss, (sx, sy))

    def _draw_muzzle_light(self, surf):
        """Ánh sáng muzzle flash chiếu lên robot."""
        if self._muzzle_t < 0.05:
            return
        t  = self._muzzle_t
        cx = self._robot.cx
        cy = self._robot.cy - 80

        r = int(200 * t)
        gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        a  = int(t * 60)
        pygame.draw.circle(gs, (255, 200, 80, a), (r, r), r)
        surf.blit(gs, (cx - r, cy - r))

    def _draw_shells(self, surf):
        """Vỏ đạn bay ra."""
        for sh in self._muzzle_shells:
            a = int(sh["life"] * 220)
            if a < 10:
                continue
            shell_surf = pygame.Surface((10, 5), pygame.SRCALPHA)
            shell_surf.fill((200, 180, 60, a))
            rotated = pygame.transform.rotate(shell_surf, sh["rot"] % 360)
            surf.blit(rotated, (int(sh["x"]) - 5, int(sh["y"]) - 2))

    # ─── Crosshair & HUD ──────────────────────────────────────

    def _draw_crosshair_custom(self):
        mx, my = pygame.mouse.get_pos()
        t      = self._crosshair_t
        expand = int(t * 18)
        size   = 18 + expand

        # Đổi màu khi aim vào robot
        if self._aim_on_robot:
            color  = (255, 80,  80)
            center = (255, 80, 80)
        else:
            color  = (220, 220, 220)
            center = (255, 255, 255)

        gap = 7 + expand // 2

        # Vẽ với outline đen
        for ox, oy, w in [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1)]:
            # outline
            pygame.draw.line(self.screen, (0, 0, 0, 180),
                (mx - size + ox, my + oy), (mx - gap + ox, my + oy), 2)
            pygame.draw.line(self.screen, (0, 0, 0, 180),
                (mx + gap + ox, my + oy), (mx + size + ox, my + oy), 2)
            pygame.draw.line(self.screen, (0, 0, 0, 180),
                (mx + ox, my - size + oy), (mx + ox, my - gap + oy), 2)
            pygame.draw.line(self.screen, (0, 0, 0, 180),
                (mx + ox, my + gap + oy), (mx + ox, my + size + oy), 2)

        # Crosshair chính
        pygame.draw.line(self.screen, color, (mx - size, my), (mx - gap, my), 2)
        pygame.draw.line(self.screen, color, (mx + gap,  my), (mx + size, my), 2)
        pygame.draw.line(self.screen, color, (mx, my - size), (mx, my - gap), 2)
        pygame.draw.line(self.screen, color, (mx, my + gap),  (mx, my + size), 2)

        # Điểm giữa
        pygame.draw.circle(self.screen, center, (mx, my), 2)

        # Vòng aim khi bắn
        if t > 0.1:
            pygame.draw.circle(self.screen, (*color, int(t * 120)),
                (mx, my), size + 6, 1)

    def _draw_hud(self, surf):
        from src.robot_renderer import ROBOT_PALETTES
        pal = self._robot.palette

        # ─── HP Bar robot (màu theo từng robot) ───
        self._hp_bar.draw(surf)
        lbl = assets.render_text(f"{pal['name']} HP", "xs", pal["neon"],
                                  shadow=True, shadow_color=(0, 0, 0))
        surf.blit(lbl, (SCREEN_W // 2 - 200, 8))

        # ─── Mode badge (góc trên giữa, dưới HP bar) ───
        if self._countdown_mode:
            badge_c = (255, 180, 30)
            badge_t = "TIME ATTACK"
        else:
            badge_c = (100, 160, 255)
            badge_t = "NORMAL"
        badge_s = assets.render_text(badge_t, "xs", badge_c, bold=True)
        surf.blit(badge_s, (SCREEN_W//2 - badge_s.get_width()//2, 52))

        # ─── Map indicator (góc trên phải) ───
        map_icons = ["", "", ""]
        map_colors_hud = [(0,200,80),(60,140,255),(40,220,80)]
        mc = map_colors_hud[self._current_map]
        map_s = assets.render_text(f"{map_icons[self._current_map]} ROUND {self._round+1}", "sm", mc, bold=True, shadow=True)
        surf.blit(map_s, (SCREEN_W - map_s.get_width() - 16, 18))

        # ─── Wave / Kill counter — 10 chấm ───
        wave_pos = self._robots_killed % self._total_waves
        dot_x0 = SCREEN_W - 16
        dot_y  = 55
        for i in range(self._total_waves):
            ri = self._total_waves - 1 - i
            dc = ROBOT_PALETTES[i]["neon"]
            dot_x = dot_x0 - ri * 18
            if i < wave_pos:
                pygame.draw.circle(surf, dc, (dot_x, dot_y), 6)
                pygame.draw.circle(surf, (255,255,255), (dot_x, dot_y), 2)
            else:
                pygame.draw.circle(surf, (40,45,60), (dot_x, dot_y), 6)
                pygame.draw.circle(surf, (70,80,100), (dot_x, dot_y), 6, 1)

        kills_s = assets.render_text(f"KILLS: {self._robots_killed}", "sm",
            pal["neon"], bold=True, shadow=True)
        surf.blit(kills_s, (SCREEN_W - kills_s.get_width() - 16, 68))

        # ─── Score ───
        sc_surf = assets.render_text(f"SCORE: {self._score}", "md", (255,210,50), bold=True, shadow=True)
        surf.blit(sc_surf, (22, 18))

        # ─── Correct / Wrong ───
        cor = assets.render_text(f"{self._correct_count}", "sm", (50,220,100), shadow=True)
        surf.blit(cor, (22, 56))
        wc    = (220,60,60) if self._wrong_count > 0 else (120,130,150)
        wrong = assets.render_text(f"{self._wrong_count}/{MAX_WRONG_ANSWERS}", "sm", wc, shadow=True)
        surf.blit(wrong, (22+cor.get_width()+18, 56))

        # ─── Hint ───
        hint = assets.render_text("CLICK ROBOT TO SHOOT  |  ESC: EXIT", "xs", (80,90,120))
        surf.blit(hint, (SCREEN_W//2-hint.get_width()//2, SCREEN_H-28))

        # ─── Warning ───
        if self._wrong_count == MAX_WRONG_ANSWERS - 1:
            a = int(200*(0.6+0.4*math.sin(self._time*6)))
            ws = assets.render_text("⚠  LAST CHANCE!", "md", (255,60,60), bold=True)
            ws.set_alpha(a)
            surf.blit(ws, (SCREEN_W//2-ws.get_width()//2, SCREEN_H-62))

    def _draw_damage_numbers(self, surf):
        for dn in self._dmg_numbers:
            a = min(255, int(dn["life"] / 1.6 * 255))
            s = assets.render_text(dn["text"], dn["size"], dn["color"],
                                    bold=True, shadow=True)
            s.set_alpha(a)
            surf.blit(s, (int(dn["x"]) - s.get_width() // 2, int(dn["y"])))

    def _draw_vignette(self):
        """Vignette đỏ khi sai + vignette đen viền màn hình."""
        # Vignette viền đen thường trực
        vs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for i in range(60):
            t = i / 60
            a = int(120 * (1 - t) ** 2)
            pygame.draw.rect(vs, (0, 0, 0, a),
                (i, i, SCREEN_W - i * 2, SCREEN_H - i * 2), 1)
        self.screen.blit(vs, (0, 0))

        # Vignette đỏ khi sai
        if self._vignette_t > 0.05:
            rv = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            a  = int(self._vignette_t / 1.5 * 100)
            for i in range(40):
                t2 = i / 40
                ia = int(a * (1 - t2) ** 2)
                pygame.draw.rect(rv, (200, 20, 20, ia),
                    (i * 2, i * 2, SCREEN_W - i * 4, SCREEN_H - i * 4), 2)
            self.screen.blit(rv, (0, 0))

    def _draw_scanlines(self):
        """Scanline overlay cinematic."""
        sl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(sl, (0, 0, 0, 18), (0, y), (SCREEN_W, y))
        self.screen.blit(sl, (0, 0))

    def _draw_endscreen(self):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        self.screen.blit(ov, (0, 0))

        title_c = (220, 50, 50)
        title   = "MISSION FAILED"
        sub     = f"Too many wrong answers ({MAX_WRONG_ANSWERS}x)"

        for offset in [(-2, 0, (180, 20, 20)), (2, 0, (20, 40, 80))]:
            ts = assets.render_text(title, "xl", offset[2], bold=True)
            self.screen.blit(ts, (SCREEN_W // 2 - ts.get_width() // 2 + offset[0],
                                   SCREEN_H // 2 - 110 + offset[1]))
        ts = assets.render_text(title, "xl", title_c, bold=True)
        self.screen.blit(ts, (SCREEN_W // 2 - ts.get_width() // 2, SCREEN_H // 2 - 110))

        ss = assets.render_text(sub, "md", (200, 210, 240), shadow=True)
        self.screen.blit(ss, (SCREEN_W // 2 - ss.get_width() // 2, SCREEN_H // 2 - 44))

        kills_s = assets.render_text(
            f"ROBOTS ELIMINATED: {self._robots_killed}", "md", (255, 180, 50),
            bold=True, shadow=True)
        self.screen.blit(kills_s, (SCREEN_W // 2 - kills_s.get_width() // 2,
                                    SCREEN_H // 2 + 4))

        sc = assets.render_text(f"FINAL SCORE: {self._score}", "lg", (255, 210, 50),
                                  bold=True, shadow=True)
        self.screen.blit(sc, (SCREEN_W // 2 - sc.get_width() // 2, SCREEN_H // 2 + 50))

        ct = assets.render_text("PRESS ENTER / CLICK TO CONTINUE", "sm",
                                  (120, 140, 180), shadow=True)
        self.screen.blit(ct, (SCREEN_W // 2 - ct.get_width() // 2, SCREEN_H // 2 + 116))

    def _update_endscreen(self, dt, events):
        self._robot.update(dt)
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_to_result()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self._go_to_result()