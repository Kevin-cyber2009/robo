"""
multiplayer_scene.py — Chế độ 2 người chơi 
"""

import pygame
import math
import random
from src.scenes.base_scene import BaseScene
from src.constants import *
from src.assets import assets
from src.ui_components import HealthBar, Button
from src.robot_renderer import RobotRenderer
from src.question_overlay import QuestionOverlay
from src.question_manager import QuestionManager
from src.powerup_system import PowerupSystem


# ─── Constants ────────────────────────────────────────────────
P1_COLOR = (60, 160, 255)    # Xanh dương (P1)
P2_COLOR = (255, 100, 60)    # Cam đỏ (P2)
SPLIT_LINE_W = 4             # Độ rộng đường chia giữa

# Player keyboard controls
P1_KEYS = {
    "up":    [pygame.K_w],
    "down":  [pygame.K_s],
    "left":  [pygame.K_a],
    "right": [pygame.K_d],
    "shoot": [pygame.K_j],
}

P2_KEYS = {
    "up":    [pygame.K_UP],
    "down":  [pygame.K_DOWN],
    "left":  [pygame.K_LEFT],
    "right": [pygame.K_RIGHT],
    "shoot": [pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS],  # + on main keyboard and numpad
}


class PlayerState:
    def __init__(self, player_id: int):
        self.id          = player_id
        self.score       = 0
        self.wrong       = 0
        self.correct     = 0
        self.combo       = 0
        self.combo_max   = 0
        # Cursor/crosshair (cả 2 player đều dùng keyboard)
        self.cursor_x    = SCREEN_W // 4 if player_id == 1 else SCREEN_W * 3 // 4
        self.cursor_y    = SCREEN_H // 2
        self.cursor_spd  = 380     # px/s
        # Gun FX
        self.recoil      = 0.0
        self.muzzle_t    = 0.0
        # Answering state
        self.is_answering = False


class MultiplayerScene(BaseScene):

    ROBOT_ORDER  = [0,1,2,3,4,5,6,7,8,9]
    ROBOT_HP_BONUS = [0,50,-20,30,-10,80,120,-30,150,80]
    MAP_NAMES    = ["lab","space","jungle"]

    def __init__(self, screen, manager):
        super().__init__(screen, manager)

        # Question manager
        self._q_manager = QuestionManager()
        n = self._q_manager.load_files(self.state.selected_question_files)
        if n == 0:
            manager.go_to(SCENE_MENU)
            return

        # Players
        self._p1 = PlayerState(1)
        self._p2 = PlayerState(2)
        self._max_wrong = MAX_WRONG_ANSWERS   # Tổng cộng giữa 2 người

        # Wave
        self._wave_index    = 0
        self._robots_killed = 0
        self._total_waves   = 10
        self._current_map   = 0
        self._round         = 0

        # Robot
        self._spawn_robot(0)

        # Overlays — mỗi player có 1
        self._overlay1 = QuestionOverlay(screen)
        self._overlay2 = QuestionOverlay(screen)
        self._cur_zone1 = self._cur_q1 = None
        self._cur_zone2 = self._cur_q2 = None

        # Power-ups (shared)
        self._powerups = PowerupSystem()

        # FX
        self._time       = 0.0
        self._game_over  = False
        self._winner     = None     # 1 | 2 | "draw"
        self._dmg_numbers = []
        self._notifs     = []       # [(text,color,y,life,x)]
        self._transition_phase = "none"
        self._transition_t = 0.0
        self._map_transition_phase = "none"
        self._map_transition_t = 0.0
        self._robot_banner_t = 3.0

        # Intro countdown (hiện hướng dẫn 3 giây)
        self._intro_t    = 4.0     # Đếm ngược 4 giây trước khi chơi

        # Env
        self._wall_lights = self._gen_wall_lights()

        pygame.mouse.set_visible(False)   # Cả 2 player dùng keyboard

    # ─── Robot management ─────────────────────────────────────

    def _spawn_robot(self, wave_index):
        robot_idx = self.ROBOT_ORDER[wave_index % self._total_waves]
        base_hp   = float(ROBOT_MAX_HP + self.ROBOT_HP_BONUS[robot_idx])
        cycle     = wave_index // self._total_waves
        hp        = base_hp + cycle * 60
        self._robot      = RobotRenderer(SCREEN_W//2, SCREEN_H//2+55, scale=1.7,
                                          robot_index=robot_idx)
        self._robot_hp   = hp
        self._robot_max_hp = hp
        self._hp_bar     = HealthBar(SCREEN_W//2-200, 22, 400, 26)
        self._hp_bar.set_ratio(hp, hp)
        self._robot_banner_t = 3.0

    def _trigger_next_robot(self):
        self._transition_phase = "out"
        self._transition_t = 0.0
        self._wave_index  += 1
        self._robots_killed += 1
        bonus = 200 + int(self._robots_killed * 10)
        # Bonus chia theo tỷ lệ điểm
        self._p1.score += bonus // 2
        self._p2.score += bonus // 2

        if self._robots_killed > 0 and self._robots_killed % self._total_waves == 0:
            next_round = self._robots_killed // self._total_waves
            self._current_map = next_round % len(self.MAP_NAMES)
            self._round = next_round
            self._map_transition_phase = "out"
            self._map_transition_t = 0.0
            self._wall_lights = self._gen_wall_lights()

    def _gen_wall_lights(self):
        lights = []
        for i in range(6):
            lights.append({
                "x": int(80+i*(SCREEN_W-160)/5),
                "y": random.randint(40,100),
                "flicker": random.uniform(0,math.pi*2),
                "intensity": random.uniform(0.6,1.0),
                "color": random.choice([(0,140,255),(0,200,140),(160,60,255)]),
            })
        return lights

    # ─── Update ───────────────────────────────────────────────

    def update(self, dt, events):
        self._time += dt

        # Intro countdown
        if self._intro_t > 0:
            self._intro_t -= dt
            for ev in events:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.manager.go_to(SCENE_MENU)
            return

        if self._game_over:
            for ev in events:
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.manager.go_to(SCENE_MENU)
            return

        if self._transition_phase != "none":
            self._update_transition(dt)
            self._robot.update(dt)
            if self._map_transition_phase != "none":
                self._update_map_transition(dt)
            return

        self._robot.update(dt)
        self._hp_bar.update(dt)
        self._robot_banner_t = max(0.0, self._robot_banner_t - dt)

        # Power-up updates
        if not self._p1.is_answering and not self._p2.is_answering:
            collected = self._powerups.update(dt, events)
            for kind in collected:
                if kind == "heal":
                    total_wrong = self._p1.wrong + self._p2.wrong
                    if total_wrong > 0:
                        if self._p2.wrong >= self._p1.wrong:
                            self._p2.wrong -= 1
                        else:
                            self._p1.wrong -= 1
                        self._add_notif("+1 MÁU", (220,60,80), SCREEN_W//2)

        # FX decay
        self._p1.recoil  = max(0.0, self._p1.recoil - dt*10)
        self._p2.recoil  = max(0.0, self._p2.recoil - dt*10)
        self._p1.muzzle_t= max(0.0, self._p1.muzzle_t - dt*14)
        self._p2.muzzle_t= max(0.0, self._p2.muzzle_t - dt*14)

        # Notifs decay
        for n in self._notifs[:]:
            n["life"] -= dt; n["y"] -= dt*28
            if n["life"] <= 0: self._notifs.remove(n)
        for dn in self._dmg_numbers[:]:
            dn["life"] -= dt; dn["y"] += dn["vy"]*dt; dn["vy"]*=0.92
            if dn["life"] <= 0: self._dmg_numbers.remove(dn)

        # P1 và P2 keyboard cursor movement
        keys = pygame.key.get_pressed()
        
        # P1 cursor (WASD)
        spd1 = self._p1.cursor_spd * dt
        if any(keys[k] for k in P1_KEYS["up"]):    self._p1.cursor_y -= spd1
        if any(keys[k] for k in P1_KEYS["down"]):  self._p1.cursor_y += spd1
        if any(keys[k] for k in P1_KEYS["left"]):  self._p1.cursor_x -= spd1
        if any(keys[k] for k in P1_KEYS["right"]): self._p1.cursor_x += spd1
        # Clamp P1 to left half
        self._p1.cursor_x = max(10, min(SCREEN_W//2-SPLIT_LINE_W//2-10, self._p1.cursor_x))
        self._p1.cursor_y = max(10, min(SCREEN_H-10, self._p1.cursor_y))
        
        # P2 cursor (Arrow keys)
        spd2 = self._p2.cursor_spd * dt
        if any(keys[k] for k in P2_KEYS["up"]):    self._p2.cursor_y -= spd2
        if any(keys[k] for k in P2_KEYS["down"]):  self._p2.cursor_y += spd2
        if any(keys[k] for k in P2_KEYS["left"]):  self._p2.cursor_x -= spd2
        if any(keys[k] for k in P2_KEYS["right"]): self._p2.cursor_x += spd2
        # Clamp P2 to right half
        self._p2.cursor_x = max(SCREEN_W//2+SPLIT_LINE_W//2+10, min(SCREEN_W-10, self._p2.cursor_x))
        self._p2.cursor_y = max(10, min(SCREEN_H-10, self._p2.cursor_y))

        # Overlays
        r1 = self._overlay1.update(dt, events)
        if r1 is not None:
            self._p1.is_answering = False
            self._process_answer(1, r1)

        r2 = self._overlay2.update(dt, events)
        if r2 is not None:
            self._p2.is_answering = False
            self._process_answer(2, r2)

        # Shooting (keyboard only)
        if not self._p1.is_answering and not self._p2.is_answering:
            for ev in events:
                if ev.type == pygame.KEYDOWN:
                    # P1 shoot with J
                    if any(ev.key == k for k in P1_KEYS["shoot"]):
                        self._do_shoot(1, (int(self._p1.cursor_x), int(self._p1.cursor_y)))
                    # P2 shoot with 1
                    elif any(ev.key == k for k in P2_KEYS["shoot"]):
                        self._do_shoot(2, (int(self._p2.cursor_x), int(self._p2.cursor_y)))
                    elif ev.key == pygame.K_ESCAPE:
                        self.manager.go_to(SCENE_MENU)

    def _do_shoot(self, player_id, pos):
        zone = self._robot.check_hit(pos[0], pos[1])
        if zone:
            q = self._q_manager.get_question_for_zone(zone)
            if q:
                p = self._p1 if player_id == 1 else self._p2
                p.recoil  = 1.0
                p.muzzle_t= 1.0
                p.is_answering = True
                
                # Keyboard nav keys for each player
                if player_id == 1:
                    nav_keys = {"up": P1_KEYS["up"], "down": P1_KEYS["down"],
                                "left": P1_KEYS["left"], "right": P1_KEYS["right"],
                                "select": P1_KEYS["shoot"]}
                    self._cur_zone1 = zone; self._cur_q1 = q
                    self._overlay1.show(q, zone, keyboard_nav=True, nav_keys=nav_keys, use_timer=False)
                else:
                    nav_keys = {"up": P2_KEYS["up"], "down": P2_KEYS["down"],
                                "left": P2_KEYS["left"], "right": P2_KEYS["right"],
                                "select": P2_KEYS["shoot"]}
                    self._cur_zone2 = zone; self._cur_q2 = q
                    self._overlay2.show(q, zone, keyboard_nav=True, nav_keys=nav_keys, use_timer=False)
                
                self._powerups.maybe_drop(self._robot.cx, self._robot.cy)

    def _process_answer(self, player_id, is_correct):
        p    = self._p1 if player_id == 1 else self._p2
        zone = self._cur_zone1 if player_id == 1 else self._cur_zone2
        q    = self._cur_q1    if player_id == 1 else self._cur_q2

        color = P1_COLOR if player_id == 1 else P2_COLOR
        name  = f"P{player_id}"
        side_x = SCREEN_W // 4 if player_id == 1 else SCREEN_W * 3 // 4

        if is_correct:
            dmg = {ZONE_HEAD_KEY:DAMAGE_HEAD, ZONE_BODY_KEY:DAMAGE_BODY, ZONE_LIMB_KEY:DAMAGE_LIMB}.get(zone,40)
            pts = {ZONE_HEAD_KEY:SCORE_HEAD,  ZONE_BODY_KEY:SCORE_BODY,  ZONE_LIMB_KEY:SCORE_LIMB}.get(zone,100)
            speed_mult = getattr(self._overlay1 if player_id==1 else self._overlay2, "last_score_mult", 1.0)
            p.combo += 1; p.combo_max = max(p.combo_max, p.combo)
            combo_mult = min(1.0+(p.combo-1)*0.25, 3.0)
            final_pts = int(pts * speed_mult * combo_mult)
            p.score   += final_pts
            p.correct += 1
            self._robot_hp -= dmg
            self._robot_hp  = max(0.0, self._robot_hp)
            self._robot.trigger_hit(zone)
            self._hp_bar.set_ratio(self._robot_hp, self._robot_max_hp)
            self._add_notif(f"{name} +{final_pts}{'' if speed_mult>1 else ''}", color, side_x)
            if p.combo >= 2:
                cc = [(255,200,50),(255,140,30),(255,80,80)][min(p.combo-2,2)]
                self._add_notif(f"{name} COMBO ×{p.combo}!", cc, side_x)
            if self._robot_hp <= 0:
                self._robot.trigger_death()
                self._trigger_next_robot()
        else:
            p.combo = 0
            p.wrong += 1
            self._add_notif(f"{name} SAI!", (220,60,60), side_x)
            total_wrong = self._p1.wrong + self._p2.wrong
            if total_wrong >= self._max_wrong:
                self._end_game()

        if player_id == 1: self._cur_zone1 = self._cur_q1 = None
        else:               self._cur_zone2 = self._cur_q2 = None

    def _end_game(self):
        self._game_over = True
        if self._p1.score > self._p2.score:
            self._winner = 1
        elif self._p2.score > self._p1.score:
            self._winner = 2
        else:
            self._winner = "draw"

    def _add_notif(self, text, color, x):
        self._notifs.append({"text":text,"color":color,"y":float(SCREEN_H//2-80),
                              "life":2.0,"x":float(x)})

    def _update_transition(self, dt):
        FADE_OUT=0.8; FADE_IN=0.7
        self._transition_t += dt
        if self._transition_phase=="out":
            if self._transition_t>=FADE_OUT:
                self._spawn_robot(self._wave_index)
                self._transition_phase="in"; self._transition_t=0.0
        elif self._transition_phase=="in":
            if self._transition_t>=FADE_IN:
                self._transition_phase="none"; self._transition_t=0.0

    def _update_map_transition(self, dt):
        MAP_FADE=1.8; self._map_transition_t+=dt
        if self._map_transition_phase=="out":
            if self._map_transition_t>=MAP_FADE:
                self._map_transition_phase="in"; self._map_transition_t=0.0
        elif self._map_transition_phase=="in":
            if self._map_transition_t>=MAP_FADE:
                self._map_transition_phase="none"; self._map_transition_t=0.0

    # ─── Draw ─────────────────────────────────────────────────

    def draw(self):
        surf = self.screen

        # Background theo map
        self._draw_bg(surf)

        # Robot (trung tâm)
        self._robot.draw(surf)
        self._hp_bar.draw(surf)

        # Power-up items
        self._powerups.draw(surf, self._time)
        self._powerups.draw_hud(surf)

        # Damage numbers
        for dn in self._dmg_numbers:
            a = min(255, int(dn["life"]/1.6*255))
            s = assets.render_text(dn["text"],"md",dn["color"],bold=True,shadow=True)
            s.set_alpha(a); surf.blit(s,(int(dn["x"])-s.get_width()//2,int(dn["y"])))

        # Notifs
        for n in self._notifs:
            a = min(255, int(n["life"]/2.0*255))
            ns = assets.render_text(n["text"],"lg",n["color"],bold=True,shadow=True)
            ns.set_alpha(a); surf.blit(ns,(int(n["x"])-ns.get_width()//2,int(n["y"])))

        # P1 crosshair (keyboard - WASD)
        self._draw_crosshair(surf, int(self._p1.cursor_x), int(self._p1.cursor_y),
                             P1_COLOR, self._p1.muzzle_t)

        # P2 crosshair (keyboard - arrows)
        self._draw_crosshair(surf, int(self._p2.cursor_x), int(self._p2.cursor_y),
                             P2_COLOR, self._p2.muzzle_t)

        # Divider
        pygame.draw.rect(surf,(180,180,220),(SCREEN_W//2-SPLIT_LINE_W//2,0,SPLIT_LINE_W,SCREEN_H))

        # HUDs (trái P1, phải P2)
        self._draw_player_hud(surf, self._p1, 10, P1_COLOR, "WASD+J")
        self._draw_player_hud(surf, self._p2, SCREEN_W//2+10, P2_COLOR, "ARROWS+")

        # Robot banner
        if self._robot_banner_t > 0:
            self._draw_robot_banner(surf)

        # Overlays (P1=trái, P2=phải — vẽ sau)
        if self._p1.is_answering:
            self._overlay1.draw()
        if self._p2.is_answering:
            self._overlay2.draw()

        # Transitions
        if self._transition_phase != "none":
            self._draw_transition(surf)
        if self._map_transition_phase != "none":
            self._draw_map_transition(surf)

        if self._game_over:
            self._draw_game_over(surf)

        # Intro countdown overlay (vẽ trên tất cả)
        if self._intro_t > 0:
            self._draw_intro(surf)

    # ─── Draw helpers ─────────────────────────────────────────

    def _draw_bg(self, surf):
        surf.fill((8,10,20))
        hz = SCREEN_H // 2
        for y in range(SCREEN_H):
            t = abs(y-hz)/hz
            if y < hz:
                c = (int(8+t*10), int(10+t*18), int(20+t*35))
            else:
                c = (int(8+t*6),  int(12+t*8),  int(22+t*10))
            pygame.draw.line(surf,c,(0,y),(SCREEN_W,y))
        # Floor grid
        vp = SCREEN_W//2
        map_neons = [(0,180,80),(40,100,255),(20,200,60)]
        nc = map_neons[self._current_map]
        for i in range(1,12):
            t=(i/11)**1.6; y=int(hz+(SCREEN_H-hz)*t)
            c=nc if i%3==0 else (25,30,50)
            pygame.draw.line(surf,c,(0,y),(SCREEN_W,y),2 if i%3==0 else 1)
        for i in range(15):
            angle=(i/14-0.5)*1.8
            ex=vp+int(math.tan(angle)*(SCREEN_H-hz)*1.1)
            pygame.draw.line(surf,(20,30,55),(vp,hz),(ex,SCREEN_H))

    def _draw_crosshair(self, surf, cx, cy, color, muzzle):
        size = 14 + int(muzzle*8)
        gap  = 5  + int(muzzle*6)
        pygame.draw.line(surf,color,(cx-size,cy),(cx-gap,cy),2)
        pygame.draw.line(surf,color,(cx+gap,cy),(cx+size,cy),2)
        pygame.draw.line(surf,color,(cx,cy-size),(cx,cy-gap),2)
        pygame.draw.line(surf,color,(cx,cy+gap),(cx,cy+size),2)
        pygame.draw.circle(surf,color,(cx,cy),2+int(muzzle*3))
        # Aim detection highlight
        if self._robot.check_hit(cx, cy):
            r=18+int(muzzle*4)
            s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(s,(*color,80),(r,r),r,2)
            surf.blit(s,(cx-r,cy-r))

    def _draw_player_hud(self, surf, p, x, color, ctrl_hint):
        hw = SCREEN_W//2 - 10
        # BG panel
        bg = pygame.Surface((hw, 70), pygame.SRCALPHA)
        bg.fill((*color, 18))
        surf.blit(bg,(x,0))
        pygame.draw.line(surf,color,(x,70),(x+hw,70),1)

        # Player label
        pl = assets.render_text(f"P{p.id}", "lg", color, bold=True, shadow=True)
        surf.blit(pl,(x+10, 8))

        # Score
        sc = assets.render_text(f"{p.score}", "md", (255,230,80), bold=True)
        surf.blit(sc,(x+60, 10))

        # Wrong count (hearts)
        for i in range(self._max_wrong):
            hx = x+hw-40-i*26; hy=14
            hc = (220,60,60) if i >= self._max_wrong-p.wrong else (50,20,20)
            pygame.draw.circle(surf,hc,(hx,hy),9)
            if i < self._max_wrong-p.wrong:
                pygame.draw.circle(surf,(255,100,120),(hx-2,hy-3),4)

        # Correct/wrong
        cs = assets.render_text(f"{p.correct} {p.wrong}", "sm", (180,200,180))
        surf.blit(cs,(x+60, 42))

        # Combo
        if p.combo >= 2:
            cc = [(255,200,50),(255,140,30),(255,80,80)][min(p.combo-2,2)]
            cb = assets.render_text(f"×{p.combo}", "md", cc, bold=True)
            surf.blit(cb,(x+hw-60,8))

        # Control hint at bottom
        ch = assets.render_text(ctrl_hint,"xs",(80,90,120))
        surf.blit(ch,(x+hw//2-ch.get_width()//2, SCREEN_H-24))

    def _draw_robot_banner(self, surf):
        t = self._robot_banner_t; a = min(1.0,t/0.5) if t<0.5 else 1.0
        pal = self._robot.palette
        name_s = assets.render_text(pal["name"],"xl",pal["neon"],bold=True,shadow=True)
        sub_s  = assets.render_text(pal["title"],"sm",(200,210,240),shadow=True)
        name_s.set_alpha(int(a*255)); sub_s.set_alpha(int(a*255))
        surf.blit(name_s,(SCREEN_W//2-name_s.get_width()//2,SCREEN_H//2-name_s.get_height()-8))
        surf.blit(sub_s, (SCREEN_W//2-sub_s.get_width()//2, SCREEN_H//2+8))

    def _draw_transition(self, surf):
        FADE_OUT=0.8; FADE_IN=0.7
        if self._transition_phase=="out":
            progress=min(1.0,self._transition_t/FADE_OUT)
        else:
            progress=max(0.0,1.0-self._transition_t/FADE_IN)
        a=int(progress*255)
        if a<=0: return
        fade=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        fade.fill((0,0,0,a)); surf.blit(fade,(0,0))
        if self._transition_phase=="out" and progress>0.75:
            from src.robot_renderer import ROBOT_PALETTES
            next_idx=self.ROBOT_ORDER[self._wave_index%self._total_waves]
            pal=ROBOT_PALETTES[next_idx]
            ta=int((progress-0.75)/0.25*255)
            ns=assets.render_text(f"ENEMY #{self._wave_index+1}","md",pal["neon"],bold=True)
            ns.set_alpha(ta); surf.blit(ns,(SCREEN_W//2-ns.get_width()//2,SCREEN_H//2-40))
            ts=assets.render_text(pal["name"],"xl",pal["neon"],bold=True)
            ts.set_alpha(ta); surf.blit(ts,(SCREEN_W//2-ts.get_width()//2,SCREEN_H//2))

    def _draw_map_transition(self, surf):
        MAP_FADE=1.8
        if self._map_transition_phase=="out":
            progress=min(1.0,self._map_transition_t/MAP_FADE)
        else:
            progress=max(0.0,1.0-self._map_transition_t/MAP_FADE)
        a=int(progress*255)
        if a<=0: return
        fade=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        fade.fill((0,0,0,a)); surf.blit(fade,(0,0))
        if progress>0.5:
            map_names=["PHÒNG THÍ NGHIỆM","TRẠM VŨ TRỤ","RỪNG NEON"]
            map_colors=[(0,200,80),(60,140,255),(40,220,80)]
            ta=int((progress-0.5)/0.5*255)
            mc=map_colors[self._current_map]
            rs=assets.render_text(f"ROUND {self._round+1}","md",(180,180,200),bold=True)
            rs.set_alpha(ta); surf.blit(rs,(SCREEN_W//2-rs.get_width()//2,SCREEN_H//2-60))
            ms=assets.render_text(map_names[self._current_map],"xl",mc,bold=True)
            ms.set_alpha(ta); surf.blit(ms,(SCREEN_W//2-ms.get_width()//2,SCREEN_H//2))

    def _draw_intro(self, surf):
        """Màn intro 4 giây: hướng dẫn điều khiển + countdown."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 8, 210))
        surf.blit(overlay, (0, 0))

        t = self._intro_t
        cy = SCREEN_H // 2

        # Title
        title = assets.render_text("CHẾ ĐỘ 2 NGƯỜI CHƠI", "xl", (255,220,80), bold=True, shadow=True)
        surf.blit(title, (SCREEN_W//2 - title.get_width()//2, cy - 170))

        # Controls panels side by side
        for i, (pid, color, lines) in enumerate([
            (1, P1_COLOR, ["P1 — WASD + J", "W/A/S/D để di chuyển", "J để bắn robot", "WASD/J để chọn đáp án"]),
            (2, P2_COLOR, ["P2 — ARROWS + +", "Phím mũi tên để di chuyển", "Phím + để bắn robot", "Arrows/+ để chọn đáp án"]),
        ]):
            px = SCREEN_W//4 + i*(SCREEN_W//2) - 200
            ps = pygame.Surface((400, 200), pygame.SRCALPHA)
            pygame.draw.rect(ps, (*color, 25), ps.get_rect(), border_radius=14)
            pygame.draw.rect(ps, (*color, 160), ps.get_rect(), width=2, border_radius=14)
            surf.blit(ps, (px, cy - 100))
            for j, line in enumerate(lines):
                lc = color if j == 0 else (200, 210, 230)
                ls = assets.render_text(line, "sm" if j == 0 else "xs", lc, bold=(j==0), shadow=True)
                surf.blit(ls, (px + 200 - ls.get_width()//2, cy - 88 + j * 44))

        # Countdown
        count = max(1, int(t))
        pulse = 0.85 + 0.15 * math.sin(self._time * 6)
        cs = assets.render_text(str(count), "xl", (255, 200, 60), bold=True, shadow=True)
        cw = int(cs.get_width() * pulse); ch = int(cs.get_height() * pulse)
        cs2 = pygame.transform.scale(cs, (max(1,cw), max(1,ch)))
        surf.blit(cs2, (SCREEN_W//2 - cw//2, cy + 120))

        hint = assets.render_text("Chuẩn bị...", "sm", (160, 170, 200))
        surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, cy + 185))

    def _draw_game_over(self, surf):
        overlay=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        overlay.fill((0,0,0,200)); surf.blit(overlay,(0,0))

        # Winner announcement
        if self._winner=="draw":
            wt="HÒA!"; wc=(255,220,80)
        elif self._winner==1:
            wt="P1 CHIẾN THẮNG!"; wc=P1_COLOR
        else:
            wt="P2 CHIẾN THẮNG!"; wc=P2_COLOR

        pulse=0.9+0.1*math.sin(self._time*4)
        ws=assets.render_text(wt,"xl",wc,bold=True,shadow=True)
        ws2=pygame.transform.scale(ws,(int(ws.get_width()*pulse),int(ws.get_height()*pulse)))
        surf.blit(ws2,(SCREEN_W//2-ws2.get_width()//2,SCREEN_H//2-120))

        # Scoreboard
        for i,(p,c) in enumerate([(self._p1,P1_COLOR),(self._p2,P2_COLOR)]):
            bx=SCREEN_W//2-260+i*280; by=SCREEN_H//2-30
            bg=pygame.Surface((240,140),pygame.SRCALPHA)
            pygame.draw.rect(bg,(*c,30),bg.get_rect(),border_radius=12)
            pygame.draw.rect(bg,(*c,150),bg.get_rect(),width=2,border_radius=12)
            surf.blit(bg,(bx,by))
            pl=assets.render_text(f"P{p.id}","xl",c,bold=True)
            surf.blit(pl,(bx+120-pl.get_width()//2,by+10))
            sc=assets.render_text(f"{p.score}","lg",(255,230,80),bold=True)
            surf.blit(sc,(bx+120-sc.get_width()//2,by+52))
            stats=assets.render_text(f"{p.correct}  {p.wrong}  MAX×{p.combo_max}","sm",c)
            surf.blit(stats,(bx+120-stats.get_width()//2,by+100))

        hint=assets.render_text("Nhấn phím bất kỳ để về Menu","sm",(150,160,180))
        surf.blit(hint,(SCREEN_W//2-hint.get_width()//2,SCREEN_H//2+150))