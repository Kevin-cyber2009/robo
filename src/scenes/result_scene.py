"""
result_scene.py - Màn hình Tổng Kết 
"""
import pygame
import math
from src.scenes.base_scene import BaseScene
from src.constants import *
from src.assets import assets
from src.ui_components import Button, Panel, ScrollList, draw_title_bar
from src.ranking import RankingSystem


class ResultScene(BaseScene):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self._ranking = RankingSystem()
        self._time    = 0.0
        self._mode    = "result"   # "result" | "review"

        answered = self.state.answered_questions
        self._rank = self._ranking.add_entry(
            self.state.player_name,
            self.state.current_score,
            self.state.correct_count,
            self.state.wrong_count,
            len(answered),
        )

        # === Xây danh sách CÂU ĐÃ LÀM (result mode) ===
        items_all = []
        for i, q in enumerate(answered):
            icon = "✓" if q["correct"] else "✗"
            zone_labels = {ZONE_HEAD_KEY:"[Đầu]", ZONE_BODY_KEY:"[Thân]", ZONE_LIMB_KEY:"[Chi]"}
            zone = zone_labels.get(q["zone"], "")
            text = f"{icon} {zone} {q['question'][:70]}{'...' if len(q['question'])>70 else ''}"
            items_all.append({"id":str(i),"text":text,"badge":"✓" if q["correct"] else "✗"})

        self._history_list = ScrollList(SCREEN_W//2-400, 390, 800, 200, item_h=44)
        self._history_list.set_items(items_all)

        # === Xây danh sách CÂU SAI (review mode) ===
        wrong_qs = [(i,q) for i,q in enumerate(answered) if not q["correct"]]
        self._wrong_items = wrong_qs

        # Review scroll list
        review_items = []
        for i, (orig_idx, q) in enumerate(wrong_qs):
            review_items.append({"id":str(i), "text":f"Câu {orig_idx+1}: {q['question'][:60]}{'...' if len(q['question'])>60 else ''}", "badge":"?"})
        self._review_list = ScrollList(SCREEN_W//2-440, 140, 880, 440, item_h=52)
        self._review_list.set_items(review_items)

        self._selected_wrong = None   # Index vào wrong_items
        self._review_scroll  = 0

        # Buttons
        cx = SCREEN_W // 2
        self._btn_retry  = Button(cx-280, SCREEN_H-76, 200, BUTTON_H, "Chơi Lại",
                                   bg_normal=GREEN_DIM, bg_hover=GREEN, color_normal=WHITE, font_size="md", icon="↺")
        self._btn_menu   = Button(cx-60,  SCREEN_H-76, 200, BUTTON_H, "Menu Chính",
                                   color_normal=GRAY, bg_hover=GRAY_DARK, font_size="md", icon="←")
        self._btn_review = Button(cx+160, SCREEN_H-76, 200, BUTTON_H, f"Xem Câu Sai ({len(wrong_qs)})",
                                   bg_normal=ORANGE_DIM, bg_hover=ORANGE,
                                   color_normal=WHITE, font_size="sm", icon="📖")
        self._btn_back   = Button(cx-100, SCREEN_H-76, 200, BUTTON_H, "← Kết Quả",
                                   color_normal=GRAY, bg_hover=GRAY_DARK, font_size="md")

        # Animation
        self._display_score = 0
        self._stars   = self._calc_stars()
        self._combo_max = getattr(self.state, "combo_max", 0)

    def _calc_stars(self):
        total = self.state.correct_count + self.state.wrong_count
        if total == 0: return 0
        r = self.state.correct_count / total
        return 3 if r >= 0.9 else (2 if r >= 0.6 else (1 if r > 0 else 0))

    def update(self, dt, events):
        self._time += dt
        target = self.state.current_score
        if self._display_score < target:
            self._display_score = min(target, self._display_score + max(1, int(target * dt * 3)))

        if self._mode == "result":
            self._history_list.update(events)
            self._btn_retry.update(events, dt)
            self._btn_menu.update(events, dt)
            self._btn_review.update(events, dt)
            if self._btn_retry.clicked:  self.manager.go_to(SCENE_START)
            if self._btn_menu.clicked:   self.manager.go_to(SCENE_MENU)
            if self._btn_review.clicked and self._wrong_items:
                self._mode = "review"; self._selected_wrong = None

        elif self._mode == "review":
            self._review_list.update(events)
            self._btn_back.update(events, dt)
            self._btn_retry.update(events, dt)
            if self._btn_back.clicked:  self._mode = "result"
            if self._btn_retry.clicked: self.manager.go_to(SCENE_START)

            # Click vào item review → xem chi tiết
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Check review_list items
                    for i, item in enumerate(self._wrong_items):
                        pass  # handled by scroll list highlight

    def draw(self):
        self.screen.fill(DARK_BG)
        self._draw_stars_bg()
        if self._mode == "result":
            self._draw_result_mode()
        else:
            self._draw_review_mode()

    # ─── RESULT MODE ─────────────────────────────────────────

    def _draw_result_mode(self):
        draw_title_bar(self.screen, "KẾT QUẢ", f"Người chơi: {self.state.player_name}")
        cx = SCREEN_W // 2

        # Rank badge
        rank_text  = f"#{self._rank}"
        rank_color = YELLOW if self._rank <= 3 else CYAN
        rank_surf  = assets.render_text(rank_text, "xl", rank_color, bold=True)
        self.screen.blit(rank_surf, (cx - rank_surf.get_width()//2, 80))
        rl = assets.render_text("Xếp Hạng", "xs", GRAY)
        self.screen.blit(rl, (cx - rl.get_width()//2, 80 + rank_surf.get_height()))

        # Score
        sp = Panel(cx-160, 148, 320, 80, alpha=200); sp.draw(self.screen)
        ss = assets.render_text(str(self._display_score), "xl", YELLOW, bold=True)
        self.screen.blit(ss, (cx - ss.get_width()//2, 156))
        pl = assets.render_text("ĐIỂM SỐ", "xs", GRAY)
        self.screen.blit(pl, (cx - pl.get_width()//2, 210))

        self._draw_stars(cx, 244)
        self._draw_stats(cx, 288)

        # Combo max badge
        if self._combo_max >= 2:
            cb_colors = [(255,200,50),(255,140,30),(255,80,80),(200,60,255),(60,220,255)]
            cc = cb_colors[min(self._combo_max-2, len(cb_colors)-1)]
            cbs = Panel(cx+170, 148, 130, 60, alpha=180); cbs.draw(self.screen)
            cbl = assets.render_text(f"×{self._combo_max}", "lg", cc, bold=True)
            self.screen.blit(cbl, (cx+235-cbl.get_width()//2, 156))
            ct = assets.render_text("MAX COMBO", "xs", cc)
            self.screen.blit(ct, (cx+235-ct.get_width()//2, 194))

        # History
        hist_lbl = assets.render_text("Câu đã làm:", "sm", CYAN, bold=True)
        self.screen.blit(hist_lbl, (SCREEN_W//2-400, 366))
        self._history_list.draw(self.screen)

        self._btn_retry.draw(self.screen)
        self._btn_menu.draw(self.screen)
        if self._wrong_items:
            self._btn_review.draw(self.screen)

    # ─── REVIEW MODE ─────────────────────────────────────────

    def _draw_review_mode(self):
        draw_title_bar(self.screen, "📖 XEM LẠI CÂU SAI",
                       f"Tổng {len(self._wrong_items)} câu sai")

        if not self._wrong_items:
            msg = assets.render_text("🎉 Không có câu sai nào! Hoàn hảo!", "lg", GREEN, bold=True)
            self.screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H//2 - 30))
        else:
            # Panel chia đôi
            left_x  = SCREEN_W//2 - 440
            right_x = SCREEN_W//2 + 10
            mid_y   = 80

            # LEFT: danh sách câu sai
            lbl = assets.render_text("Câu sai:", "sm", ORANGE, bold=True)
            self.screen.blit(lbl, (left_x, mid_y + 4))

            # Render từng câu sai
            y = mid_y + 30
            for i, (orig_idx, q) in enumerate(self._wrong_items):
                iy = y + i * 60
                if iy > SCREEN_H - 120: break

                # Row bg
                is_sel = (self._selected_wrong == i)
                bg_c = (20,40,60) if is_sel else (14,18,30)
                bg_s = pygame.Surface((420, 52), pygame.SRCALPHA)
                bg_s.fill((*bg_c, 220))
                border_c = ORANGE if is_sel else (40,50,70)
                pygame.draw.rect(bg_s, (*border_c,), bg_s.get_rect(), width=1+(1 if is_sel else 0), border_radius=6)
                self.screen.blit(bg_s, (left_x, iy))

                # Click detection
                row_rect = pygame.Rect(left_x, iy, 420, 52)
                mx, my = pygame.mouse.get_pos()
                if row_rect.collidepoint(mx, my):
                    hover_s = pygame.Surface((420,52), pygame.SRCALPHA)
                    hover_s.fill((40,80,120,40))
                    self.screen.blit(hover_s, (left_x, iy))
                    for ev in pygame.event.get(pygame.MOUSEBUTTONDOWN):
                        if ev.button == 1:
                            self._selected_wrong = i

                # Number badge
                num_s = assets.render_text(f"#{orig_idx+1}", "xs", ORANGE, bold=True)
                self.screen.blit(num_s, (left_x+8, iy+4))

                # Question text
                qt = q["question"][:55] + ("..." if len(q["question"])>55 else "")
                qt_s = assets.render_text(qt, "xs", WHITE if is_sel else GRAY_LIGHT)
                self.screen.blit(qt_s, (left_x+8, iy+22))

                # Zone badge
                zone_label = {ZONE_HEAD_KEY:"ĐẦU",ZONE_BODY_KEY:"THÂN",ZONE_LIMB_KEY:"CHI"}.get(q["zone"],"")
                zone_c = {ZONE_HEAD_KEY:ZONE_HEAD,ZONE_BODY_KEY:ZONE_BODY,ZONE_LIMB_KEY:ZONE_LIMB}.get(q["zone"],CYAN)
                zl_s = assets.render_text(zone_label, "xs", zone_c)
                self.screen.blit(zl_s, (left_x+400-zl_s.get_width()-6, iy+4))

            # RIGHT: chi tiết câu đang chọn
            if self._selected_wrong is not None and self._selected_wrong < len(self._wrong_items):
                self._draw_review_detail(right_x, mid_y, self._wrong_items[self._selected_wrong])
            else:
                hint = assets.render_text("← Chọn câu để xem chi tiết", "sm", (60,80,110))
                self.screen.blit(hint, (right_x+80, SCREEN_H//2))

        self._btn_back.draw(self.screen)
        self._btn_retry.draw(self.screen)

    def _draw_review_detail(self, rx, ry, item):
        orig_idx, q = item
        pw  = SCREEN_W - rx - 20
        pad = 16

        # Panel
        ph  = SCREEN_H - ry - 90
        ps  = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(ps, (12,16,32,230), ps.get_rect(), border_radius=12)
        pygame.draw.rect(ps, (*ORANGE_DIM,180), ps.get_rect(), width=2, border_radius=12)
        self.screen.blit(ps, (rx, ry))

        # Header
        hdr = assets.render_text(f"Câu {orig_idx+1}  —  {q['zone'].upper()}", "sm", ORANGE, bold=True)
        self.screen.blit(hdr, (rx+pad, ry+pad))

        y = ry + pad + hdr.get_height() + 10
        # Divider
        pygame.draw.line(self.screen, (*ORANGE_DIM,120), (rx+pad,y), (rx+pw-pad,y))
        y += 10

        # Question text
        qt_s = assets.render_text_wrapped(q["question"], pw-pad*2, "sm", WHITE, bold=True)
        self.screen.blit(qt_s, (rx+pad, y)); y += qt_s.get_height()+14

        # Choices (nếu MC)
        if q["type"] == Q_MULTIPLE_CHOICE and q.get("choices"):
            correct_key = str(q.get("answer","")).upper()
            for key, text in sorted(q["choices"].items()):
                is_correct = key.upper() == correct_key
                c = GREEN if is_correct else (80,90,110)
                prefix = "✓ " if is_correct else "   "
                choice_s = assets.render_text_wrapped(f"{prefix}{key}. {text}", pw-pad*2-8, "xs", c)
                if is_correct:
                    bg_s = pygame.Surface((pw-pad*2, choice_s.get_height()+6), pygame.SRCALPHA)
                    bg_s.fill((20,60,30,120))
                    self.screen.blit(bg_s, (rx+pad, y-3))
                self.screen.blit(choice_s, (rx+pad+4, y)); y += choice_s.get_height()+6

        y += 10
        pygame.draw.line(self.screen, (*ORANGE_DIM,80), (rx+pad,y), (rx+pw-pad,y))
        y += 10

        # Đáp án đúng
        ans = q.get("answer","")
        if isinstance(ans, dict):
            ans_str = "  |  ".join(f"{k}: {'Đúng' if v else 'Sai'}" for k,v in ans.items())
        else:
            ans_str = str(ans)
        al = assets.render_text("ĐÁP ÁN ĐÚNG:", "xs", YELLOW, bold=True)
        self.screen.blit(al, (rx+pad, y)); y += al.get_height()+4
        av = assets.render_text_wrapped(ans_str, pw-pad*2, "sm", GREEN, bold=True)
        self.screen.blit(av, (rx+pad, y)); y += av.get_height()+10

        # Type badge
        type_labels = {Q_MULTIPLE_CHOICE:"Trắc nghiệm",Q_SHORT_ANSWER:"Trả lời ngắn",Q_FACT_ANALYSIS:"Phân tích dữ kiện"}
        tl = assets.render_text(f"Dạng: {type_labels.get(q['type'],'?')}", "xs", GRAY)
        self.screen.blit(tl, (rx+pad, ry+ph-tl.get_height()-8))

    # ─── Shared drawing helpers ───────────────────────────────

    def _draw_stars(self, cx, y):
        for i in range(3):
            filled = i < self._stars
            star_x = cx - 60 + i * 60
            color  = YELLOW if filled else GRAY_DARK
            pulse  = math.sin(self._time * 2 + i) * 0.1 + 1.0 if filled else 1.0
            r      = int(18 * pulse)
            pts    = []
            for j in range(10):
                angle = math.radians(j * 36 - 90)
                radius = r if j % 2 == 0 else r // 2
                pts.append((star_x + math.cos(angle)*radius, y + math.sin(angle)*radius))
            if filled: pygame.draw.polygon(self.screen, color, pts)
            else:      pygame.draw.polygon(self.screen, color, pts, width=2)

    def _draw_stats(self, cx, y):
        stats = [
            ("✓ Đúng",  str(self.state.correct_count), GREEN),
            ("✗ Sai",   str(self.state.wrong_count),   RED),
            ("📝 Tổng", str(self.state.correct_count + self.state.wrong_count), CYAN),
        ]
        for i, (label, value, color) in enumerate(stats):
            ix = cx - 330 + i * 220 + 110
            vs = assets.render_text(value, "lg", color, bold=True)
            ls = assets.render_text(label, "xs", GRAY)
            self.screen.blit(vs, (ix - vs.get_width()//2, y))
            self.screen.blit(ls, (ix - ls.get_width()//2, y+40))

    def _draw_stars_bg(self):
        import random
        rng = random.Random(42)
        for _ in range(50):
            x = rng.randint(0, SCREEN_W); y = rng.randint(0, SCREEN_H)
            r = rng.randint(1, 2)
            alpha = int(rng.randint(30,100) * (0.7+0.3*math.sin(self._time+x*0.01)))
            s = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*WHITE, alpha), (r,r), r)
            self.screen.blit(s, (x,y))