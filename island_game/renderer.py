"""All drawing/rendering functions. Separated from game logic."""

import math, random, pygame
from config import *
from ui import Button, draw_bar, draw_panel, font, draw_text_center

# ────────────────── Shared state (set by Game) ──────────────────
_ach_popup = None
_ach_popup_timer = 0.0


def trigger_ach_popup(name, desc):
    global _ach_popup, _ach_popup_timer
    _ach_popup = (name, desc)
    _ach_popup_timer = 3.0


# ────────────────── Background ──────────────────
def draw_sky(surface, t, night_mode, day_progress=0.5):
    """Draw sky with time-of-day coloring.
    day_progress: 0=midnight, 0.25=dawn, 0.5=noon, 0.75=dusk, 1.0=midnight
    """
    # Interpolate sky colors based on time of day
    if day_progress < 0.25:  # midnight to dawn
        frac = day_progress / 0.25
        r0, g0, b0 = 8, 8, 25
        r1, g1, b1 = int(80*frac), int(120*frac), int(180*frac)
    elif day_progress < 0.5:  # dawn to noon
        frac = (day_progress - 0.25) / 0.25
        r0, g0, b0 = 80, 120, 180
        r1, g1, b1 = int(80+20*frac), int(170+10*frac), int(230+20*frac)
    elif day_progress < 0.75:  # noon to dusk
        frac = (day_progress - 0.5) / 0.25
        r0, g0, b0 = int(100-20*frac), int(180-60*frac), int(250-50*frac)
        r1, g1, b1 = int(45+155*frac), int(110+100*frac), int(200+55*frac)
    else:  # dusk to midnight
        frac = (day_progress - 0.75) / 0.25
        r0, g0, b0 = int(80-72*frac), int(50-42*frac), int(150-125*frac)
        r1, g1, b1 = int(200-180*frac), int(210-190*frac), int(255-230*frac)

    for y in range(0, SH//2 + 30, 4):
        frac = y / (SH//2 + 30)
        r = int(r0*(1-frac) + r1*frac)
        g = int(g0*(1-frac) + g1*frac)
        b = int(b0*(1-frac) + b1*frac)
        pygame.draw.line(surface, (r, g, b), (0, y), (SW, y))

    # Sun/Moon based on time
    if 0.2 < day_progress < 0.8:  # Sun visible during day
        sun_y = 75 + int(math.sin((day_progress - 0.2) / 0.6 * math.pi) * 100)
        pulse = math.sin(t * 2) * 5
        pygame.draw.circle(surface, (255, 230, 60), (SW - 110, sun_y + int(pulse)), 38)
        for i in range(8):
            a = i * math.pi / 4 + t * 0.4
            ex = int(SW-110 + math.cos(a)*55); ey = int(sun_y + math.sin(a)*55)
            pygame.draw.line(surface, (255,200,0), (ex,ey),
                             (int(SW-110+math.cos(a)*68), int(sun_y+math.sin(a)*68)), 2)
    else:  # Moon at night
        moon_y = 70 + int(math.sin((day_progress - 0.75) / 0.5 * math.pi) * 80) if day_progress > 0.75 else 70
        pygame.draw.circle(surface, (220,215,180), (110, moon_y), 34)
        pygame.draw.circle(surface, (int(r0*0.5), int(g0*0.5), int(b0*0.5)), (120, moon_y-6), 34)


def draw_stars(surface, t):
    rng = random.Random(42)
    stars = [(rng.randint(50,SW-50), rng.randint(20,SH//2-30)) for _ in range(80)]
    for sx, sy in stars:
        alpha = 0.3 + 0.7*abs(math.sin(t*1.5 + sx*0.05))
        bri = int(255*alpha)
        c = (bri, bri, int(bri*0.9))
        pygame.draw.circle(surface, c, (sx, sy), 1 if alpha < 0.6 else 2)


def draw_ocean(surface, wave_t):
    for y in range(SH//2-10, SH, 4):
        frac = (y - SH//2 + 10) / (SH - SH//2 + 10)
        r = int(25*(1-frac)+13*frac); g = int(120*(1-frac)+68*frac); b = int(200*(1-frac)+155*frac)
        pygame.draw.line(surface, (r,g,b), (0,y), (SW,y))
    wave_offsets = [i*0.5 for i in range(8)]
    for wi, woy in enumerate(wave_offsets):
        wy = SH//2-5+wi*16+int(math.sin(wave_t+woy)*5)
        pts = [(x, wy+int(math.sin(x*0.018+wave_t*1.5+woy)*3)) for x in range(0,SW+20,20)]
        for i in range(len(pts)-1):
            pygame.draw.line(surface, (255,255,255), pts[i], pts[i+1], 1)


def draw_clouds(surface, cloud_t, night_mode):
    rng = random.Random(7)
    offsets = rng.sample(range(SW+200), 5)
    speeds = [0.08, 0.12, 0.06, 0.10, 0.09]
    sizes = [50, 40, 60, 45, 55]
    y_pos = [60, 100, 75, 110, 55]
    base_b = 60 if night_mode else 220
    for i,(cx,spd,cs,cy) in enumerate(zip(offsets, speeds, sizes, y_pos)):
        nx = int((cx + cloud_t*spd*SW) % (SW+cs*2) - cs)
        col = (base_b, base_b, int(base_b*1.06))
        for dx,dy,dr in [(0,0,cs*0.4),(cs*0.3,cs*0.1,cs*0.3),(cs*0.6,cs*0.05,cs*0.25),(cs*0.15,cs*0.15,cs*0.2)]:
            pygame.draw.circle(surface, col, (nx+int(dx), int(cy+dy)), int(dr))


def draw_weather(surface, weather, particle_sys):
    if weather == "rainy":
        particle_sys.rain(SW//2, 0, 8, (100,140,255))
    elif weather == "stormy":
        particle_sys.rain(SW//2, 0, 12, (80,100,180))
        if random.random() < 0.005:
            lt = pygame.Surface((SW,SH), pygame.SRCALPHA); lt.fill((200,220,255,40)); surface.blit(lt,(0,0))
    elif weather == "foggy":
        fog = pygame.Surface((SW,SH), pygame.SRCALPHA); fog.fill((110,120,135,50)); surface.blit(fog,(0,0))


def draw_island(surface):
    pts = [(x, int(SH*0.58+math.sin(x*0.012)*18+math.cos(x*0.025)*9)) for x in range(0,SW+1,3)]
    if pts:
        pygame.draw.polygon(surface, C_SAND, [(x,SH) for x in range(0,SW+1,3)] + pts[::-1])
        pygame.draw.lines(surface, (210,175,100), False, pts, 3)
    g_pts = [(x, int(SH*0.42+math.sin(x*0.015+1)*14+math.cos(x*0.03)*8)) for x in range(80,SW-80,3)]
    if g_pts:
        pygame.draw.polygon(surface, C_GRASS, [(x,SH) for x in range(80,SW-80,3)] + g_pts[::-1])
    trees = [(200,SH*0.5),(350,SH*0.48),(500,SH*0.46),(900,SH*0.5),(1050,SH*0.47),(1180,SH*0.52)]
    for tx,ty in trees:
        pygame.draw.rect(surface, C_BROWN, (tx-3,ty,6,18))
        pygame.draw.circle(surface, (40,110,40), (tx,ty-5), 14)
        pygame.draw.circle(surface, (50,130,50), (tx-8,ty+2), 10)
        pygame.draw.circle(surface, (45,120,45), (tx+8,ty+2), 10)
    for rx in [620,780,1100]:
        ry = SH*0.55
        pygame.draw.ellipse(surface, C_STONE, (rx-12,ry-6,24,14))


# ────────────────── HUD ──────────────────
def draw_hud(surface, p, weather):
    draw_bar(surface, 20, 18, 200, 20, p.health, p.max_health, C_HEALTH)
    surface.blit(font("xs").render(f"HP {p.health}/{p.max_health}", True, WHITE), (25,20))
    draw_bar(surface, 20, 44, 200, 20, p.hunger, 100, C_HUNGER)
    surface.blit(font("xs").render(f"饱腹 {p.hunger}", True, WHITE), (25,46))
    draw_bar(surface, 20, 70, 200, 20, p.energy, 100, C_ENERGY)
    surface.blit(font("xs").render(f"体力 {p.energy}", True, BLACK), (25,72))
    surface.blit(font("md").render(f"第 {p.day} 天", True, C_GOLD), (20,96))
    surface.blit(font("xs").render(f"Lv{p.level} exp={p.exp}", True, (180,180,180)), (20,132))
    # Weapon/Armor
    wp = p.weapon or "无"
    if p.weapon and p.weapon in p.dur:
        d = p.dur[p.weapon]; col = C_SUCCESS if d>15 else C_HUNGER if d>5 else C_HEALTH
        surface.blit(font("sm").render(f"武器: {wp}({d})", True, col), (20,156))
    else:
        surface.blit(font("sm").render(f"武器: {wp}", True, (140,140,140)), (20,156))
    ar = p.armor or "无"
    if p.armor and p.armor in p.dur:
        d = p.dur[p.armor]; col = C_SUCCESS if d>15 else C_HUNGER if d>5 else C_HEALTH
        surface.blit(font("sm").render(f"护甲: {ar}({d})", True, col), (20,180))
    else:
        surface.blit(font("sm").render(f"护甲: {ar}", True, (140,140,140)), (20,180))
    # Weather
    wi_map = {"sunny":"[晴]","cloudy":"[阴]","rainy":"[雨]","stormy":"[暴]","foggy":"[雾]"}
    wc_map = {"sunny":C_GOLD,"cloudy":(180,180,180),"rainy":C_OCEAN,"stormy":C_STORM,"foggy":(150,150,170)}
    surface.blit(font("xs").render(wi_map.get(weather,"[晴]"), True, wc_map.get(weather,WHITE)), (SW-80,20))


# ────────────────── Action Bar ──────────────────
def build_action_bar(surface, p, quest, mouse_pos=None):
    """Build and draw action buttons. Returns list of (category, label/id, Button)."""
    bar_h = 120; bar_y = SH - bar_h - 10
    panel = pygame.Surface((SW-40, bar_h), pygame.SRCALPHA); panel.fill((5,8,20,210))
    surface.blit(panel, (20, bar_y))
    pygame.draw.rect(surface, C_BORDER, (20, bar_y, SW-40, bar_h), 2, border_radius=10)

    btns = []
    r1 = bar_y + 8; r2 = bar_y + 65
    configs_r1 = [
        ("action","捕捞",  30,  r1, 120, 50, C_OCEAN),
        ("action","探索", 160,  r1, 120, 50, C_GRASS),
        ("action","进食", 290,  r1, 120, 50, C_HUNGER),
        ("action","治疗", 420,  r1, 120, 50, C_SUCCESS),
        ("action","建造", 550,  r1, 120, 50, C_BROWN),
        ("action","制作", 680,  r1, 120, 50, C_STONE),
        ("action","成就", 810,  r1, 120, 50, C_GOLD),
        ("action","下一天",940, r1, 140, 50, C_WARNING),
    ]
    configs_r2 = [
        ("sys","背包",  30,  r2, 140, 44, (40,40,60)),
        ("sys","任务", 180,  r2, 140, 44, (60,30,30) if quest else (30,30,45)),
        ("sys","S1",   330,  r2,  80, 44, (20,50,80)),
        ("sys","S2",   420,  r2,  80, 44, (20,50,80)),
        ("sys","S3",   510,  r2,  80, 44, (20,50,80)),
    ]
    for cat, label, bx, by, bw, bh, bg in configs_r1 + configs_r2:
        btn = Button(bx, by, bw, bh, label, bg)
        btn.draw(surface, mouse_pos)
        btns.append((cat, label, btn))
    return btns


def draw_messages(surface, messages):
    y = SH - 178
    for msg, life in messages[-4:]:
        alpha = min(255, int(255*life/3.0))
        t = font("sm").render(msg, True, (150,220,100)); t.set_alpha(alpha)
        surface.blit(t, (25, y)); y -= 26


def draw_quest_info(surface, quest):
    if not quest: return
    pw,ph = 260,115; x,y = SW-280, 10
    draw_panel(surface, x, y, pw, ph, "当前任务")
    surface.blit(font("sm").render(quest.title, True, C_GOLD), (x+15, y+60))
    surface.blit(font("xs").render(quest.desc[:22], True, C_TEXT_DIM), (x+15, y+82))
    ratio = quest.current/quest.need if quest.need > 0 else 0
    draw_bar(surface, x+15, y+102, pw-30, 10, ratio*100, 100, C_OCEAN)


# ────────────────── Overlay Panels ──────────────────
def draw_inventory(surface, p, mouse_pos=None):
    pw,ph = 600,480; px=(SW-pw)//2; py=(SH-ph)//2
    draw_panel(surface, px, py, pw, ph, "背包")
    close = Button(px+pw-70, py+12, 58, 34, "关闭", (80,40,40)); close.draw(surface, mouse_pos)
    btns = [("inv_close", close)]
    items = list(p.inventory.items()); col_n = 4
    ix, iy, cw, ch = px+25, py+75, (pw-50)//4, 60
    for idx,(item,count) in enumerate(items):
        r,c = idx//col_n, idx%col_n; cx,cy = ix+c*cw, iy+r*ch
        pygame.draw.rect(surface, (25,30,50), (cx,cy,cw-5,ch-5), border_radius=6)
        pygame.draw.rect(surface, C_BORDER, (cx,cy,cw-5,ch-5), 1, border_radius=6)
        surface.blit(font("sm").render(f"{item} x{count}", True, WHITE), (cx+6,cy+8))
        if item in p.dur:
            d=p.dur[item]; col_d=C_SUCCESS if d>15 else C_HUNGER if d>5 else C_HEALTH
            surface.blit(font("xs").render(f"耐久:{d}", True, col_d), (cx+6,cy+30))
    if not items:
        t=font("sm").render("背包是空的", True, C_TEXT_DIM)
        surface.blit(t, (px+pw//2-t.get_width()//2, py+ph//2))
    story = Button(px+pw//2-80, py+ph-60, 160, 44, f"故事 ({len(p.pages_found)}/8)", (40,30,60))
    story.draw(surface, mouse_pos); btns.append(("story_btn", story))
    return btns


def draw_craft(surface, p, mouse_pos=None):
    from data import RECIPES
    pw,ph = 700,500; px=(SW-pw)//2; py=(SH-ph)//2
    draw_panel(surface, px, py, pw, ph, "合成制作")
    close = Button(px+pw-70, py+12, 58, 34, "关闭", (80,40,40)); close.draw(surface, mouse_pos)
    btns = [("craft_close", close)]
    iy = py+72
    for name,(cost,itype,stat,dur) in RECIPES.items():
        can = all(p.has(i)>=n for i,n in cost.items())
        bg = (30,80,40) if can else (35,35,45)
        surface.blit(font("sm").render(name, True, C_SUCCESS if can else C_TEXT_DIM), (px+25,iy+4))
        cs = " ".join(f"{i}x{n}" for i,n in cost.items())
        surface.blit(font("xs").render(cs, True, (130,160,130) if can else (90,90,90)), (px+25,iy+26))
        bt = Button(px+pw-120, iy+2, 100, 36, "制作", bg); bt.draw(surface, mouse_pos)
        btns.append(("craft", name, bt)); iy += 54
        if iy+54 > py+ph-80: break
    return btns


def draw_build(surface, p, mouse_pos=None):
    from data import BUILDINGS
    pw,ph = 700,500; px=(SW-pw)//2; py=(SH-ph)//2
    draw_panel(surface, px, py, pw, ph, "建造建筑")
    close = Button(px+pw-70, py+12, 58, 34, "关闭", (80,40,40)); close.draw(surface, mouse_pos)
    btns = [("build_close", close)]
    iy = py+72
    for name,(cost,effect) in BUILDINGS.items():
        done = name in p.buildings; can = all(p.has(i)>=n for i,n in cost.items()) and not done
        bg = (30,70,30) if can else (35,35,45) if not done else (20,50,20)
        lab = "已建成" if done else ("建造" if can else "材料不足")
        col = C_SUCCESS if can else (100,200,100) if done else C_TEXT_DIM
        surface.blit(font("sm").render(name, True, col), (px+25,iy+4))
        info = f"{effect} | {' '.join(f'{i}x{n}' for i,n in cost.items())}"
        surface.blit(font("xs").render(info, True, (120,160,120) if can else (90,90,90)), (px+25,iy+26))
        bt = Button(px+pw-100, iy+2, 85, 36, lab, bg); bt.draw(surface, mouse_pos)
        btns.append(("build", name, bt)); iy += 54
        if iy+54 > py+ph-80: break
    return btns


def draw_ach(surface, p, mouse_pos=None):
    from data import ACHIEVEMENTS
    pw,ph = 520,420; px=(SW-pw)//2; py=(SH-ph)//2
    draw_panel(surface, px, py, pw, ph, "成就")
    close = Button(px+pw-70, py+12, 58, 34, "关闭", (80,40,40)); close.draw(surface, mouse_pos)
    btns = [("ach_close", close)]
    iy = py+72
    for a in ACHIEVEMENTS:
        u = a["id"] in p.achievements; col = C_GOLD if u else C_TEXT_DIM
        surface.blit(font("sm").render(("[*] " if u else "[ ] ")+a["name"], True, col), (px+25,iy+2))
        surface.blit(font("xs").render(a["desc"], True, (180,180,100) if u else (130,130,130)), (px+35,iy+24))
        iy += 48
    return btns


def draw_story(surface, p, mouse_pos=None):
    from data import STORIES
    pw,ph = 680,500; px=(SW-pw)//2; py=(SH-ph)//2
    draw_panel(surface, px, py, pw, ph, f"漂流故事 ({len(p.pages_found)}/8)", C_GOLD)
    close = Button(px+pw-70, py+12, 58, 34, "关闭", (80,40,40)); close.draw(surface, mouse_pos)
    btns = [("story_close", close)]
    iy = py+72
    for s in STORIES:
        if s["id"] in p.pages_found:
            surface.blit(font("sm").render(f'{s["id"]}. {s["title"]}', True, C_GOLD), (px+25,iy+2))
            preview = s["text"][:40]+"..."
            surface.blit(font("xs").render(preview, True, (160,160,120)), (px+35,iy+24))
            bt = Button(px+pw-100, iy+2, 85, 36, "阅读", (40,60,40)); bt.draw(surface, mouse_pos)
            btns.append(("read_story", s["id"], bt)); iy += 54
            if iy+54 > py+ph-80: break
    if not p.pages_found:
        t=font("sm").render("尚未发现任何故事...", True, C_TEXT_DIM)
        surface.blit(t, (px+pw//2-t.get_width()//2, py+ph//2))
    return btns


def draw_story_detail(surface, story, mouse_pos=None):
    pw,ph = 700,500; px=(SW-pw)//2; py=(SH-ph)//2
    draw_panel(surface, px, py, pw, ph, story["title"], C_GOLD)
    close = Button(px+pw-70, py+12, 58, 34, "关闭", (80,40,40)); close.draw(surface, mouse_pos)
    iy = py+70; words = story["text"]
    line = ""
    for ch in words:
        if len(line) >= 35:
            surface.blit(font("sm").render(line, True, (200,200,180)), (px+30,iy)); iy+=28; line = ""
        line += ch
    if line:
        surface.blit(font("sm").render(line, True, (200,200,180)), (px+30,iy))
    return [("story_detail_close", close)]


def draw_quest_log(surface, qlog, quest, mouse_pos=None):
    pw,ph = 480,450; px=(SW-pw)//2; py=(SH-ph)//2
    draw_panel(surface, px, py, pw, ph, "任务日志")
    close = Button(px+pw-70, py+12, 58, 34, "关闭", (80,40,40)); close.draw(surface, mouse_pos)
    btns = [("qlog_close", close)]
    iy = py+72
    if not qlog:
        t=font("sm").render("暂无任务记录", True, C_TEXT_DIM)
        surface.blit(t, (px+pw//2-t.get_width()//2, py+ph//2))
    else:
        for st,title,desc in qlog[-8:]:
            col = C_SUCCESS if st=="完成" else C_HUNGER
            surface.blit(font("sm").render(f"[{st}] {title[:15]}", True, col), (px+25,iy+2))
            surface.blit(font("xs").render(desc[:30], True, (140,140,140)), (px+35,iy+22))
            iy += 38
    if quest and not quest.completed:
        surface.blit(font("sm").render(f"[进行中] {quest.title}", True, C_GOLD), (px+25,iy+8))
        surface.blit(font("xs").render(quest.desc[:30], True, C_TEXT_DIM), (px+35,iy+28))
    return btns


# ────────────────── Combat UI ──────────────────
def draw_combat(surface, php, pmhp, ehp, emhp, ename, patk, pdef, eatk, edfs, clog,
                mouse_pos=None, enemy_sprite=None, enemy_row=0, enemy_anim=None, enemy_hit_flash=0.0):
    for y in range(0, SH//2, 4):
        f = y / (SH//2)
        pygame.draw.line(surface,
            (int(50*(1-f)+20*f), int(30*(1-f)+100*f), int(60*(1-f)+180*f)), (0, y), (SW, y))
    pw, ph = 900, 500; px = (SW - pw) // 2; py = (SH - ph) // 2
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA); panel.fill((5, 8, 20, 230))
    surface.blit(panel, (px, py))
    pygame.draw.rect(surface, C_HEALTH, (px, py, pw, ph), 2, border_radius=15)
    surface.blit(font("lg").render(f"遭遇 {ename}", True, C_HEALTH),
                 (px + pw//2 - font("lg").size(f"遭遇 {ename}")[0]//2, py+15))
    draw_bar(surface, px+50, py+75, pw-100, 28, ehp, emhp, C_HEALTH)
    surface.blit(font("md").render(f"HP {max(0,ehp)}/{emhp}", True, WHITE),
                 (px + pw//2 - font("md").size(f"HP {max(0,ehp)}/{emhp}")[0]//2, py+78))

    # Draw enemy sprite in combat panel (left side)
    if enemy_sprite is not None and enemy_anim is not None:
        ef = enemy_anim.current_frame
        ef = pygame.transform.scale(ef, (ef.get_width()*2, ef.get_height()*2))
        sprite_x = px + 80 - ef.get_width() // 2
        sprite_y = py + ph//2 - ef.get_height() // 2 + 20
        
        # Hit flash: white overlay when damaged
        if enemy_hit_flash > 0:
            flash_alpha = int(255 * (enemy_hit_flash / 0.15))
            flash = pygame.Surface(ef.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, flash_alpha))
            ef.blit(flash, (0, 0))
        
        surface.blit(ef, (sprite_x, sprite_y))

    draw_bar(surface, px+50, py+145, pw-100, 28, php, pmhp, C_SUCCESS)
    surface.blit(font("md").render(f"你的HP {php}/{pmhp}", True, WHITE),
                 (px + pw//2 - font("md").size(f"你的HP {php}/{pmhp}")[0]//2, py+148))
    surface.blit(font("sm").render(f"攻击{patk} 防御{pdef}", True, (180, 180, 180)),
                 (px + pw//2 - font("sm").size(f"攻击{patk} 防御{pdef}")[0]//2, py+178))
    log_y = py + 210
    for line in clog[-5:]:
        surface.blit(font("sm").render(line, True, C_TEXT_DIM), (px+50, log_y)); log_y += 28
    btns = []
    for label, bx, bw, bg in [
            ("攻击", 60, 180, C_HEALTH), ("防御", 260, 180, C_OCEAN),
            ("道具", 460, 180, C_SUCCESS), ("逃跑", 660, 180, C_STONE)]:
        btn = Button(px+bx, py+ph-100, bw, 60, label, bg); btn.draw(surface, mouse_pos)
        btns.append(("combat", label, btn))
    return btns


# ────────────────── Intro & Ending ──────────────────
def draw_intro(surface, page, total, typed_text, t_val):
    surface.fill((5,8,20))
    surface.blit(font("sm").render(f"{page+1}/{total}", True, (100,100,100)), (SW-80,20))
    ti=font("md").render("荒岛求生", True, C_GOLD)
    surface.blit(ti, (SW//2-ti.get_width()//2, SH//2-80))
    ty=SH//2-30
    for line in typed_text.split("\n"):
        surface.blit(font("sm").render(line, True, WHITE), (100,ty)); ty+=36
    draw_bar(surface, 100, SH-80, SW-200, 12, (page+1)/total*100, 100, C_OCEAN)
    surface.blit(font("xs").render("按任意键跳过...", True, (80,80,80)), (SW-180, SH-30))
    pygame.display.flip()


def draw_ending(surface, etype, edata, p, mouse_pos=None):
    surface.fill(edata.get("color", (20,20,40)))
    col = edata.get("color", WHITE)
    ti = font("xl").render(edata.get("title","游戏结束"), True, col)
    surface.blit(ti, (SW//2-ti.get_width()//2, SH//2-160))
    stats = [f"生存天数: {p.day}",f"捕捞次数: {p.fish_count}",f"击败敌人: {p.enemy_kills}",
             f"建造数量: {p.build_count}",f"故事收集: {len(p.pages_found)}/8"]
    y=SH//2-60
    for s in stats:
        t=font("md").render(s, True, WHITE); surface.blit(t, (SW//2-t.get_width()//2, y)); y+=50
    btn=Button(SW//2-80, SH//2+180, 160, 56, "重新开始", C_WARNING); btn.draw(surface, mouse_pos)
    return [("ending_restart", btn)]


def draw_ach_popup(surface):
    global _ach_popup, _ach_popup_timer
    if not _ach_popup: return
    _ach_popup_timer -= 0.016
    if _ach_popup_timer <= 0: _ach_popup = None; return
    name, desc = _ach_popup
    alpha = min(255, int(255 * _ach_popup_timer / 1.0))
    pw,ph = 340,70; px=SW-pw-20; py=20
    panel=pygame.Surface((pw,ph),pygame.SRCALPHA); panel.fill((20,30,60,int(alpha*0.9)))
    surface.blit(panel,(px,py))
    pygame.draw.rect(surface, C_GOLD, (px,py,pw,ph), 2, border_radius=8)
    t=font("sm").render(f"成就解锁: {name}", True, C_GOLD); t.set_alpha(alpha); surface.blit(t,(px+15,py+8))
    t=font("xs").render(desc, True, (200,200,200)); t.set_alpha(alpha); surface.blit(t,(px+15,py+38))
