"""
question_overlay.py - Overlay Câu Hỏi (v2 - Time Attack + Power-ups)
"""
import pygame, math, re
from src.constants import *
from src.assets import assets
from src.ui_components import Button, TextInput

# ── Timer theo độ khó ──────────────────────────────────────
TIMER_BY_DIFF = {"easy": 15.0, "medium": 10.0, "hard": 8.0}
SPEED_BONUS_THRESHOLD = 3.0   # Trả lời trong 3s đầu → ×2

def _normalize_number(s: str):
    s = s.strip().replace(",", ".")
    s = re.sub(r'[a-zA-Z%°]+$', '', s).strip()
    try: return float(s)
    except ValueError: return None

def _numbers_match(user: str, correct: str) -> bool:
    u_num = _normalize_number(user)
    c_num = _normalize_number(correct)
    if u_num is not None and c_num is not None:
        c_str = str(correct).strip().replace(",", ".")
        if "." in c_str:
            decimals = len(c_str.rstrip("0").split(".")[1]) if "." in c_str else 0
            tol = 0.5 * (10 ** (-decimals)) + 1e-9
        else:
            tol = 0.01
        return abs(u_num - c_num) <= tol
    return user.strip().lower() == correct.strip().lower()

def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class QuestionOverlay:
    STATE_HIDDEN = "hidden"
    STATE_SHOW   = "show"
    STATE_RESULT = "result"

    def __init__(self, screen: pygame.Surface):
        self.screen   = screen
        self._state   = self.STATE_HIDDEN
        self._question= None
        self._zone    = None
        self._result  = None
        self._result_timer   = 0.0
        self._slide_y = SCREEN_H
        self._time    = 0.0

        # ── Time Attack ────────────────────────────────────────
        self._timer_max   = 15.0   # Đặt lại khi show()
        self._timer       = 15.0
        self._time_up     = False
        self._slow_time   = False  # Power-up: Slow Time (timer freeze)
        self._hint_used   = False  # Power-up: Hint Reveal
        self._hint_key    = None   # Key bị ẩn (đáp án sai)

        # ── Speed bonus ───────────────────────────────────────
        self.last_score_mult = 1.0   # Đọc từ gameplay sau khi answer

        self._fa_checkboxes  = {}
        self._mc_buttons     = {}
        self._sa_input       = None
        self._btn_sa_submit  = None
        self._btn_fa_submit  = None
        self._pending_result = None
        self._panel_x = SCREEN_W // 2 - 440
        self._panel_w = 880

    @property
    def is_visible(self):
        return self._state != self.STATE_HIDDEN

    # ── Show / Hide ────────────────────────────────────────────
    def show(self, question: dict, zone: str, slow_time=False, hint_reveal=False, use_timer=True, keyboard_nav=False, nav_keys=None):
        self._question   = question
        self._zone       = zone
        self._state      = self.STATE_SHOW
        self._result     = None
        self._slide_y    = SCREEN_H
        self._time       = 0.0
        self._pending_result = None
        self._time_up    = False
        self._hint_used  = hint_reveal
        self._hint_key   = None
        self._slow_time  = slow_time
        self._use_timer  = use_timer          # False = không đếm ngược
        self._keyboard_nav = keyboard_nav      # True = multiplayer keyboard navigation
        self._nav_keys   = nav_keys or {}     # Keys for navigation {"up":[], "down":[], "left":[], "right":[], "select":[]}
        self.last_score_mult = 1.0

        # Multiple choice / True-False: cursor position
        self._selected_index = 0  # Default A or True
        
        # Double-click tracking for keyboard nav
        self._last_select_time = 0.0  # Time of last select key press
        self._double_click_window = 0.4  # 400ms window for double-click

        # Set timer — nếu không dùng timer thì đặt rất lớn (vô hạn thực tế)
        diff = question.get("difficulty", "medium")
        base = TIMER_BY_DIFF.get(diff, 10.0) if use_timer else 999.0
        self._timer_max = base
        self._timer     = base

        # Hint: chọn 1 key sai ngẫu nhiên để "hé lộ" (làm xám đi)
        if hint_reveal and question["type"] == Q_MULTIPLE_CHOICE:
            import random
            correct = str(question["answer"]).upper()
            wrong_keys = [k for k in question.get("choices", {}) if k.upper() != correct]
            if wrong_keys:
                self._hint_key = random.choice(wrong_keys)

        pygame.mouse.set_visible(not keyboard_nav)  # Hide mouse in multiplayer
        self._build_ui()

    def _hide(self):
        self._state = self.STATE_HIDDEN
        pygame.mouse.set_visible(False)

    # ── Build UI ───────────────────────────────────────────────
    def _build_ui(self):
        px = self._panel_x; pw = self._panel_w
        q  = self._question
        if q["type"] == Q_MULTIPLE_CHOICE:
            self._mc_buttons = {}
            for key, text in q.get("choices", {}).items():
                btn = Button(0, 0, pw//2-28, 52, text, font_size="sm",
                             bg_normal=(22,28,48), bg_hover=CYAN_DIM,
                             color_normal=WHITE, color_hover=WHITE)
                btn._key_label = key
                self._mc_buttons[key] = btn
        elif q["type"] == Q_SHORT_ANSWER:
            self._sa_input = TextInput(px+24, 0, pw-48, 54, placeholder="Nhập số / đáp án...")
            self._sa_input.active = True
            self._btn_sa_submit = Button(SCREEN_W//2-90, 0, 180, 48, "XÁC NHẬN  ",
                                          bg_normal=GREEN_DIM, bg_hover=GREEN,
                                          color_normal=WHITE, font_size="sm")
        elif q["type"] == Q_FACT_ANALYSIS:
            self._fa_checkboxes = {}
            for key in sorted(q.get("choices", {}).keys()):
                self._fa_checkboxes[key] = {
                    "true":  Button(0,0,88,40,"Đúng",bg_normal=GREEN_DIM,bg_hover=GREEN,color_normal=WHITE,font_size="xs"),
                    "false": Button(0,0,88,40,"Sai", bg_normal=(80,25,25),bg_hover=RED,color_normal=WHITE,font_size="xs"),
                    "selected": None,
                }
            self._btn_fa_submit = Button(SCREEN_W//2-90, 0, 180, 48, "XÁC NHẬN  ",
                                          bg_normal=CYAN_DIM, bg_hover=CYAN,
                                          color_normal=WHITE, font_size="sm")

    # ── Update ─────────────────────────────────────────────────
    def update(self, dt, events):
        self._time += dt
        self._slide_y += (0 - self._slide_y) * min(dt*12, 1.0)

        if self._state == self.STATE_HIDDEN: return None
        if self._state == self.STATE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0:
                result = self._pending_result
                self._pending_result = None
                self._hide()
                return result
            return None
        if self._state == self.STATE_SHOW:
            # Timer countdown
            if not self._slow_time:
                self._timer -= dt
            if self._timer <= 0 and not self._time_up:
                self._time_up = True
                self._submit_answer("__TIMEOUT__")
            return self._update_question(dt, events)
        return None

    def _update_question(self, dt, events):
        q_type = self._question["type"]
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self._hide(); return None
        if   q_type == Q_MULTIPLE_CHOICE: return self._update_mc(events, dt)
        elif q_type == Q_SHORT_ANSWER:    return self._update_sa(events, dt)
        elif q_type == Q_FACT_ANALYSIS:   return self._update_fa(events, dt)
        return None

    def _update_mc(self, events, dt):
        import time
        
        # Keyboard navigation mode (multiplayer)
        if self._keyboard_nav:
            keys_list = sorted(self._mc_buttons.keys())
            if not keys_list:  # Safety check
                return None
            
            # Clamp selected index to valid range
            self._selected_index = max(0, min(len(keys_list) - 1, self._selected_index))
            
            for ev in events:
                if ev.type == pygame.KEYDOWN:
                    # Navigate up/down or left/right
                    if any(ev.key == k for k in self._nav_keys.get("up", []) + self._nav_keys.get("left", [])):
                        self._selected_index = max(0, self._selected_index - 1)
                    elif any(ev.key == k for k in self._nav_keys.get("down", []) + self._nav_keys.get("right", [])):
                        self._selected_index = min(len(keys_list) - 1, self._selected_index + 1)
                    # Double-click to submit
                    elif any(ev.key == k for k in self._nav_keys.get("select", [])):
                        current_time = time.time()
                        if current_time - self._last_select_time < self._double_click_window:
                            # Double click detected - submit
                            if self._selected_index < len(keys_list):
                                selected_key = keys_list[self._selected_index]
                                if selected_key != self._hint_key:
                                    self._submit_answer(selected_key)
                        else:
                            # Single click - just register the time
                            self._last_select_time = current_time
            return None
        
        # Mouse mode (normal)
        for key, btn in self._mc_buttons.items():
            if key == self._hint_key: continue  # Hint: disable wrong button
            btn.update(events, dt)
            if btn.clicked: self._submit_answer(key)
        return None

    def _update_sa(self, events, dt):
        import time
        
        self._sa_input.update(events, dt)
        self._btn_sa_submit.update(events, dt)
        
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                # For keyboard nav mode - double click to submit
                if self._keyboard_nav and any(ev.key == k for k in self._nav_keys.get("select", [])):
                    if self._sa_input.value.strip():
                        current_time = time.time()
                        if current_time - self._last_select_time < self._double_click_window:
                            # Double click - submit
                            self._submit_answer(self._sa_input.value)
                            return None
                        else:
                            # Single click - register time
                            self._last_select_time = current_time
                # Enter always submits (non-keyboard nav or Enter key)
                elif ev.key == pygame.K_RETURN:
                    if self._sa_input.value.strip():
                        self._submit_answer(self._sa_input.value)
                        return None
        
        if self._btn_sa_submit.clicked and self._sa_input.value.strip():
            self._submit_answer(self._sa_input.value)
        return None

    def _update_fa(self, events, dt):
        import time
        
        # Keyboard navigation mode (multiplayer)
        if self._keyboard_nav:
            keys_list = sorted(self._fa_checkboxes.keys())
            if not keys_list:  # Safety check
                return None
            
            # Clamp selected index to valid range
            self._selected_index = max(0, min(len(keys_list) - 1, self._selected_index))
            
            for ev in events:
                if ev.type == pygame.KEYDOWN:
                    # Navigate between questions
                    if any(ev.key == k for k in self._nav_keys.get("up", [])):
                        self._selected_index = max(0, self._selected_index - 1)
                    elif any(ev.key == k for k in self._nav_keys.get("down", [])):
                        self._selected_index = min(len(keys_list) - 1, self._selected_index + 1)
                    # Left/Right to toggle True/False for current question
                    elif any(ev.key == k for k in self._nav_keys.get("left", []) + self._nav_keys.get("right", [])):
                        if self._selected_index < len(keys_list):
                            key = keys_list[self._selected_index]
                            current = self._fa_checkboxes[key]["selected"]
                            self._fa_checkboxes[key]["selected"] = not current if current is not None else True
                    # Select key: single click = toggle, double click = submit
                    elif any(ev.key == k for k in self._nav_keys.get("select", [])):
                        current_time = time.time()
                        if current_time - self._last_select_time < self._double_click_window:
                            # Double click - submit if all answered
                            answers = {k: g["selected"] for k,g in self._fa_checkboxes.items()}
                            if all(v is not None for v in answers.values()):
                                self._submit_answer(answers)
                        else:
                            # Single click - toggle current question
                            if self._selected_index < len(keys_list):
                                key = keys_list[self._selected_index]
                                current = self._fa_checkboxes[key]["selected"]
                                self._fa_checkboxes[key]["selected"] = not current if current is not None else True
                            self._last_select_time = current_time
            return None
        
        # Mouse mode (normal)
        for key, grp in self._fa_checkboxes.items():
            grp["true"].update(events, dt); grp["false"].update(events, dt)
            if grp["true"].clicked:  grp["selected"] = True
            if grp["false"].clicked: grp["selected"] = False
        self._btn_fa_submit.update(events, dt)
        if self._btn_fa_submit.clicked:
            answers = {k: g["selected"] for k,g in self._fa_checkboxes.items()}
            if any(v is None for v in answers.values()): return None
            self._submit_answer(answers)
        return None

    # ── Answer checking ────────────────────────────────────────
    def _submit_answer(self, user_answer):
        q = self._question; correct = q["answer"]; q_type = q["type"]

        if user_answer == "__TIMEOUT__":
            is_correct = False
        elif q_type == Q_MULTIPLE_CHOICE:
            is_correct = str(user_answer).strip().upper() == str(correct).strip().upper()
        elif q_type == Q_SHORT_ANSWER:
            is_correct = _numbers_match(str(user_answer), str(correct))
        elif q_type == Q_FACT_ANALYSIS:
            is_correct = isinstance(user_answer, dict) and all(user_answer.get(k)==v for k,v in correct.items())
        else:
            is_correct = False

        # Speed bonus multiplier
        elapsed = self._timer_max - self._timer
        if is_correct and not self._time_up:
            if elapsed <= SPEED_BONUS_THRESHOLD:
                self.last_score_mult = 2.0
            elif elapsed <= self._timer_max * 0.4:
                self.last_score_mult = 1.5
            else:
                self.last_score_mult = 1.0
        else:
            self.last_score_mult = 1.0

        self._result = is_correct
        self._pending_result = is_correct
        self._state = self.STATE_RESULT
        self._result_timer = 2.0

    # ── Draw ───────────────────────────────────────────────────
    def draw(self):
        if self._state == self.STATE_HIDDEN: return
        self._draw_panel(int(self._slide_y))
        pygame.mouse.set_visible(True)

    def _draw_panel(self, offset):
        q = self._question
        if not q: return
        alpha = int(170 * max(0.0, 1.0 - abs(offset)/SCREEN_H))
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((0,0,0,alpha))
        self.screen.blit(dim, (0,0))

        zone_colors = {ZONE_HEAD_KEY:(220,80,80), ZONE_BODY_KEY:(80,160,220), ZONE_LIMB_KEY:(80,200,120)}
        zc = zone_colors.get(self._zone, (0,200,255))
        px = self._panel_x; pw = self._panel_w; pad = 28

        q_surf_h  = self._estimate_text_h(q["question"], pw-pad*2, "md")
        passage_h = (self._estimate_text_h(q.get("passage",""), pw-pad*2, "sm")+14) if q["type"]==Q_FACT_ANALYSIS and q.get("passage") else 0
        extra_h   = len(q.get("choices",{}))*60+40 if q["type"]==Q_MULTIPLE_CHOICE else (140 if q["type"]==Q_SHORT_ANSWER else len(q.get("choices",{}))*62+70)
        top_bar_h = 50
        timer_bar_h = 12
        ph = max(380, min(int(top_bar_h+20+q_surf_h+passage_h+extra_h+60+timer_bar_h), 660))
        py = max(20, (SCREEN_H-ph)//2) + offset

        # Panel BG + glow
        pulse = 0.6 + 0.4*math.sin(self._time*2.5)
        gs = pygame.Surface((pw+40, ph+40), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*zc, int(40*pulse)), gs.get_rect(), border_radius=20)
        self.screen.blit(gs, (px-20, py-20))
        ps = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(ps, (10,14,28,248), ps.get_rect(), border_radius=16)
        self.screen.blit(ps, (px, py))
        pygame.draw.rect(self.screen, zc, (px,py,pw,ph), width=2, border_radius=16)

        # Top bar
        bar_bg = tuple(int(c*0.4) for c in zc)
        bar_s = pygame.Surface((pw, top_bar_h), pygame.SRCALPHA)
        pygame.draw.rect(bar_s, (*bar_bg, 220), bar_s.get_rect(), border_radius=14)
        self.screen.blit(bar_s, (px, py))
        pygame.draw.rect(self.screen, zc, (px,py,pw,top_bar_h), width=2, border_radius=14)

        zone_labels = {ZONE_HEAD_KEY:"VÙNG ĐẦU  —  Câu Khó", ZONE_BODY_KEY:"VÙNG THÂN  —  Câu Trung Bình", ZONE_LIMB_KEY:"VÙNG TAY/CHÂN  —  Câu Dễ"}
        zlbl = assets.render_text(zone_labels.get(self._zone,"Câu Hỏi"), "sm", WHITE, bold=True, shadow=True, shadow_color=(0,0,0))
        self.screen.blit(zlbl, (px+20, py+(top_bar_h-zlbl.get_height())//2))

        # === TIMER BAR (ngay dưới top bar) ===
        self._draw_timer_bar(px, py+top_bar_h+2, pw)

        y = py + top_bar_h + timer_bar_h + 14
        if q["type"] == Q_FACT_ANALYSIS and q.get("passage"):
            ps_surf = assets.render_text_wrapped(q["passage"], pw-pad*2, "sm", GRAY_LIGHT)
            self.screen.blit(ps_surf, (px+pad, y)); y += ps_surf.get_height()+12
        q_surf = assets.render_text_wrapped(q["question"], pw-pad*2, "md", WHITE, bold=True)
        self.screen.blit(q_surf, (px+pad, y)); y += q_surf.get_height()+16
        pygame.draw.line(self.screen, (*zc,80), (px+pad,y), (px+pw-pad,y)); y += 12

        if self._state == self.STATE_RESULT:
            self._draw_result(px, py, pw, ph, y, zc)
        else:
            if   q["type"] == Q_MULTIPLE_CHOICE: self._draw_mc(px, y, pw, ph, pad, zc)
            elif q["type"] == Q_SHORT_ANSWER:    self._draw_sa(px, y, pw, zc)
            elif q["type"] == Q_FACT_ANALYSIS:   self._draw_fa(px, y, pw, pad)
            if self._state == self.STATE_SHOW:
                esc_lbl = assets.render_text("ESC: bỏ qua", "xs", (80,90,110))
                self.screen.blit(esc_lbl, (px+pw-esc_lbl.get_width()-14, py+ph-esc_lbl.get_height()-10))

    def _draw_timer_bar(self, px, py, pw):
        """Thanh timer đổi màu xanh→vàng→đỏ, pulse khi <=3s."""
        # Normal mode (không countdown) — hiện badge thay vì timer
        if not getattr(self, "_use_timer", True):
            lbl = assets.render_text("INF  NORMAL MODE", "xs", (100,160,255))
            self.screen.blit(lbl, (px + pw - lbl.get_width() - 8, py - 1))
            return

        ratio  = max(0.0, self._timer / self._timer_max)
        bar_w  = int((pw-8) * ratio)
        bar_h  = 10

        # Màu nền
        pygame.draw.rect(self.screen, (20,25,40), (px+4, py, pw-8, bar_h), border_radius=5)

        # Màu bar theo ratio
        if ratio > 0.6:
            color = (50, 200, 80)
        elif ratio > 0.3:
            t = (ratio - 0.3) / 0.3
            color = _lerp_color((220,180,40), (50,200,80), t)
        else:
            color = (220, 60, 60)

        # Pulse khi <= 3s
        if self._timer <= SPEED_BONUS_THRESHOLD and not self._slow_time:
            pulse = 0.7 + 0.3*math.sin(self._time * 10)
            color = tuple(min(255, int(c*pulse)) for c in color)

        if bar_w > 0:
            pygame.draw.rect(self.screen, color, (px+4, py, bar_w, bar_h), border_radius=5)

        # Slow time indicator
        if self._slow_time:
            frozen = assets.render_text("SLOW TIME", "xs", (80,200,255))
            self.screen.blit(frozen, (px + pw - frozen.get_width() - 8, py - 2))
            return

        # Timer text
        t_str = f"{self._timer:.1f}s"
        tc = (255,80,80) if self._timer <= 3 else (180,200,220)
        t_lbl = assets.render_text(t_str, "xs", tc, bold=self._timer <= 3)
        self.screen.blit(t_lbl, (px + pw - t_lbl.get_width() - 8, py - 1))

        # Speed bonus hint (khi còn thời gian trong 3s đầu)
        elapsed = self._timer_max - self._timer
        if elapsed < SPEED_BONUS_THRESHOLD and self._state == self.STATE_SHOW:
            bonus_lbl = assets.render_text("×2 SPEED BONUS!", "xs", (255,220,50))
            self.screen.blit(bonus_lbl, (px+8, py-1))

    def _draw_mc(self, px, y, pw, ph, pad, zc):
        choices = self._question.get("choices", {})
        n = len(choices); cols = 2 if n > 2 else 1
        btn_w = (pw - pad*2 - (cols-1)*12) // cols; btn_h = 54; row_gap = 10
        keys_list = sorted(choices.keys())
        
        # Safety: clamp selected index
        if self._keyboard_nav and keys_list:
            self._selected_index = max(0, min(len(keys_list) - 1, self._selected_index))
        
        for i, (key, text) in enumerate(sorted(choices.items())):
            col = i%cols; row = i//cols
            bx = px+pad+col*(btn_w+12); by = y+row*(btn_h+row_gap)
            btn = self._mc_buttons.get(key)
            if not btn: continue
            btn.rect.x=bx; btn.rect.y=by; btn.rect.w=btn_w; btn.rect.h=btn_h
            
            # Keyboard navigation: highlight selected
            is_selected = (self._keyboard_nav and i == self._selected_index)
            
            # Hint: dim wrong answer
            is_hinted = (key == self._hint_key)
            t = btn._hover_t if not is_hinted else 0
            
            # Background color
            if is_selected:
                bg = _lerp_color(CYAN_DIM, CYAN, 0.5)  # Bright highlight
            elif is_hinted:
                bg = (15,18,28)
            else:
                bg = _lerp_color((22,28,48), CYAN_DIM, t)
            
            pygame.draw.rect(self.screen, bg, btn.rect, border_radius=10)
            
            # Border (thicker if selected)
            border_w = 3 if is_selected else 2
            border_c = CYAN if is_selected else ((30,40,60) if is_hinted else (zc if t > 0.1 else (50,60,90)))
            pygame.draw.rect(self.screen, border_c, btn.rect, width=border_w, border_radius=10)
            
            badge_r=16; badge_x=bx+badge_r+10; badge_y=by+btn_h//2
            badge_c = (50,55,70) if is_hinted else zc
            pygame.draw.circle(self.screen, badge_c, (badge_x,badge_y), badge_r)
            key_s = assets.render_text(key, "sm", (80,90,100) if is_hinted else (0,0,0), bold=True)
            self.screen.blit(key_s, (badge_x-key_s.get_width()//2, badge_y-key_s.get_height()//2))
            text_x=bx+badge_r*2+18; text_area=btn_w-badge_r*2-28
            text_c = (50,60,80) if is_hinted else (WHITE if t < 0.5 else (240,250,255))
            f_size = "xs" if assets.font("sm").size(text)[0] > text_area else "sm"
            txt_s = assets.render_text_wrapped(text, text_area, f_size, text_c)
            ty = by+(btn_h-txt_s.get_height())//2
            self.screen.set_clip(pygame.Rect(text_x, by+4, text_area, btn_h-8))
            self.screen.blit(txt_s, (text_x, ty))
            self.screen.set_clip(None)
            # Hint strikethrough overlay
            if is_hinted:
                lx = bx+8; lw = btn_w-16
                pygame.draw.line(self.screen, (80,30,30), (lx, by+btn_h//2), (lx+lw, by+btn_h//2), 2)

    def _draw_sa(self, px, y, pw, zc):
        hint = assets.render_text("Nhập số (vd: 3.14  hoặc  -2.5  hoặc  1500)", "xs", (100,160,200))
        self.screen.blit(hint, (px+24, y)); y += hint.get_height()+8
        self._sa_input.rect.x=px+24; self._sa_input.rect.y=y; self._sa_input.rect.w=pw-48
        self._sa_input.draw(self.screen); y += self._sa_input.rect.h+14
        self._btn_sa_submit.rect.x=SCREEN_W//2-90; self._btn_sa_submit.rect.y=y
        self._btn_sa_submit.draw(self.screen)

    def _draw_fa(self, px, y, pw, pad):
        choices = self._question.get("choices", {})
        for i, key in enumerate(sorted(choices.keys())):
            item_y=y+i*62; grp=self._fa_checkboxes.get(key)
            if not grp: continue
            sel = grp["selected"]
            row_c = (20,60,30,80) if sel is True else ((60,20,20,80) if sel is False else (25,30,50,60))
            row_s = pygame.Surface((pw-pad*2,54), pygame.SRCALPHA)
            row_s.fill(row_c)
            self.screen.blit(row_s, (px+pad, item_y))
            grp["true"].rect.x=px+pad+8; grp["true"].rect.y=item_y+7
            grp["false"].rect.x=px+pad+104; grp["false"].rect.y=item_y+7
            if sel is True:   grp["true"].bg_normal=GREEN;   grp["false"].bg_normal=(50,25,25)
            elif sel is False: grp["true"].bg_normal=(25,50,25); grp["false"].bg_normal=RED
            else:              grp["true"].bg_normal=GREEN_DIM;  grp["false"].bg_normal=(80,25,25)
            grp["true"].draw(self.screen); grp["false"].draw(self.screen)
            text=f"{key}. {choices[key]}"
            t_surf=assets.render_text_wrapped(text, pw-pad-206-12, "sm", WHITE)
            self.screen.blit(t_surf, (px+pad+206, item_y+(54-t_surf.get_height())//2))
        sub_y=y+len(choices)*62+10
        self._btn_fa_submit.rect.x=SCREEN_W//2-90; self._btn_fa_submit.rect.y=sub_y
        self._btn_fa_submit.draw(self.screen)

    def _draw_result(self, px, py, pw, ph, y, zc):
        is_correct = self._result
        pulse = math.sin(self._time*7)*0.08+1.0
        if is_correct:
            color,icon,msg = GREEN,"","CHÍNH XÁC!"
            # Hiện speed bonus
            if self.last_score_mult > 1.0:
                mult_s = assets.render_text(f"×{self.last_score_mult:.1f} SPEED BONUS!", "md", YELLOW, bold=True, shadow=True, shadow_color=(0,0,0))
                self.screen.blit(mult_s, (px+pw//2-mult_s.get_width()//2, y+94))
        else:
            color,icon,msg = RED,"","SAI RỒI!" if not self._time_up else "HẾT GIỜ!"
            correct = self._question["answer"]
            correct_str = "  |  ".join(f"{k}: {'Đúng' if v else 'Sai'}" for k,v in correct.items()) if isinstance(correct,dict) else str(correct)
            ans = assets.render_text(f"Đáp án đúng: {correct_str}", "sm", YELLOW, shadow=True)
            self.screen.blit(ans, (px+pw//2-ans.get_width()//2, y+90))
        icon_s = assets.render_text(icon, "xl", color, bold=True)
        iw=int(icon_s.get_width()*pulse); ih=int(icon_s.get_height()*pulse)
        scaled=pygame.transform.scale(icon_s, (max(1,iw),max(1,ih)))
        self.screen.blit(scaled, (px+pw//2-iw//2, y-8))
        msg_s = assets.render_text(msg, "lg", color, bold=True, shadow=True)
        self.screen.blit(msg_s, (px+pw//2-msg_s.get_width()//2, y+56))
        t_pct=max(0.0, self._result_timer/2.0); bar_w=int((pw-48)*t_pct); bar_y=py+ph-12
        pygame.draw.rect(self.screen, (30,35,55), (px+24,bar_y,pw-48,6), border_radius=3)
        if bar_w > 0:
            pygame.draw.rect(self.screen, color, (px+24,bar_y,bar_w,6), border_radius=3)

    def _estimate_text_h(self, text, max_w, size):
        try:
            f=assets.font(size); lh=f.get_linesize()+8; cw=max(1,f.size("W")[0])
            return max(1,(len(text)//(max_w//cw)+text.count("\n")+1))*lh
        except: return 40