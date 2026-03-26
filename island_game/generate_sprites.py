#!/usr/bin/env python3
"""
Sprite generator - 程序化生成像素艺术角色和怪物精灵图。
纯用 Pygame 绘制，无外部资源依赖。
"""
import os, math, pygame, random

pygame.init()

# 画布设置
SCALE = 3          # 像素缩放
SPRITE_W = 32      # 单帧宽
SPRITE_H = 40      # 单帧高
FPS = 6            # 动画速度

OUT_DIR = os.path.join(os.path.dirname(__file__), "sprites")
os.makedirs(OUT_DIR, exist_ok=True)

def c(r, g, b):
    return (r, g, b)

# ─── 调色板 ───
SKIN_L  = c(255, 220, 170)
SKIN_M  = c(220, 175, 130)
SKIN_D  = c(180, 130,  90)
HAIR    = c( 60,  40,  20)
WHITE   = c(255, 255, 255)
BLACK   = c( 20,  20,  20)
BROWN   = c(139,  90,  43)
TAN     = c(210, 180, 110)
GREEN   = c( 56, 142,  60)
DARK_G  = c( 30,  80,  30)
RED     = c(220,  60,  60)
DARK_R  = c(150,  30,  30)
BLUE    = c( 30, 120, 200)
DARK_B  = c( 15,  70, 150)
GOLD    = c(255, 200,  50)
PURPLE  = c(140,  80, 180)
ORANGE  = c(230, 140,  30)
YELLOW  = c(255, 235,  59)
CYAN    = c( 64, 224, 208)
GRAY    = c(128, 128, 128)
DARK_GY = c( 60,  60,  60)
PINK    = c(255, 150, 180)
CORAL   = c(255, 100,  80)
TEAL    = c( 20, 160, 150)

TRANSPARENT = (0, 0, 0, 0)


class SpriteSheet:
    """生成多帧动画精灵图。"""

    def __init__(self, name, frames, anim_names):
        self.name = name
        self.frames = frames      # list of surface lists [[frame0_col0, frame0_col1], ...]
        self.anim_names = anim_names
        self.out_path = os.path.join(OUT_DIR, f"{name}.png")

    def save(self):
        # 每个动画一行，帧数 = max帧数
        max_frames = max(len(f) for f in self.frames)
        cols = len(self.frames)
        img_w = max_frames * SPRITE_W * SCALE
        img_h = cols * SPRITE_H * SCALE
        sheet = pygame.Surface((img_w, img_h), pygame.SRCALPHA)
        sheet.fill((0, 0, 0, 0))

        for row_idx, frames in enumerate(self.frames):
            for col_idx, frame in enumerate(frames):
                x = col_idx * SPRITE_W * SCALE
                y = row_idx * SPRITE_H * SCALE
                scaled = pygame.transform.scale(frame, (SPRITE_W * SCALE, SPRITE_H * SCALE))
                sheet.blit(scaled, (x, y))

        pygame.image.save(sheet, self.out_path)
        print(f"  ✓ {self.name}.png  ({cols} animations × {max_frames} frames)")
        return sheet


def make_frame(draw_fn):
    """用 draw_fn 绘制一帧，返回 Surface。"""
    surf = pygame.Surface((SPRITE_W, SPRITE_H), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    draw_fn(surf)
    return surf


def px(surf, x, y, color):
    """画一个像素点。"""
    if 0 <= x < SPRITE_W and 0 <= y < SPRITE_H:
        surf.set_at((x, y), color)


def rect(surf, x, y, w, h, color, filled=True):
    for dy in range(h):
        for dx in range(w):
            px(surf, x + dx, y + dy, color)


def ellipse(surf, cx, cy, rx, ry, color, outline=True):
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if (dx*dx)/(rx*rx) + (dy*dy)/(ry*ry) <= 1:
                px(surf, cx + dx, cy + dy, color)


# ══════════════════════════════════════════════════════
#  主角 - 存活的男人
# ══════════════════════════════════════════════════════

def draw_player_idle(surf, t=0, facing=1):
    """站立待机"""
    hflip = -1 if facing < 0 else 1
    fx = lambda x: SPRITE_W//2 + (x - SPRITE_W//2) * hflip

    # 头发
    rect(surf, fx(13), 3, 7, 4, HAIR)
    # 头
    rect(surf, fx(12), 7, 8, 8, SKIN_L)
    rect(surf, fx(13), 6, 6, 3, HAIR)
    # 眼睛
    px(surf, fx(14), 11, BLACK)
    px(surf, fx(17), 11, BLACK)
    # 嘴
    px(surf, fx(16), 14, c(200, 100, 100))
    # 身体 (棕褐色背心)
    rect(surf, fx(11), 15, 10, 10, c(139, 90, 43))
    rect(surf, fx(12), 15, 8, 10, c(160, 100, 50))
    # 手臂
    rect(surf, fx(9),  17, 3, 8, SKIN_M)
    rect(surf, fx(22), 17, 3, 8, SKIN_M)
    # 腿
    rect(surf, fx(12), 25, 4, 12, TAN)
    rect(surf, fx(17), 25, 4, 12, TAN)
    # 鞋子
    rect(surf, fx(11), 36, 6, 3, BROWN)
    rect(surf, fx(16), 36, 6, 3, BROWN)


def draw_player_walk(surf, frame=0, facing=1):
    """行走帧"""
    hflip = -1 if facing < 0 else 1
    fx = lambda x: SPRITE_W//2 + (x - SPRITE_W//2) * hflip
    bob = frame % 2 * 1

    # 头发
    rect(surf, fx(13), 3 - bob, 7, 4, HAIR)
    # 头
    rect(surf, fx(12), 7 - bob, 8, 8, SKIN_L)
    rect(surf, fx(13), 6 - bob, 6, 3, HAIR)
    # 眼睛
    px(surf, fx(14), 11 - bob, BLACK)
    px(surf, fx(17), 11 - bob, BLACK)
    # 身体
    rect(surf, fx(12), 15 - bob, 8, 10, c(160, 100, 50))
    # 手臂摆动
    arm_off = 1 if frame % 2 == 0 else -1
    rect(surf, fx(9),  17 + arm_off, 3, 8, SKIN_M)
    rect(surf, fx(22), 17 - arm_off, 3, 8, SKIN_M)
    # 腿摆动
    leg_off = 1 if frame % 2 == 0 else -1
    rect(surf, fx(12 + leg_off), 25 - bob, 4, 12, TAN)
    rect(surf, fx(17 - leg_off), 25 - bob, 4, 12, TAN)
    rect(surf, fx(11 + leg_off), 36 - bob, 6, 3, BROWN)
    rect(surf, fx(16 - leg_off), 36 - bob, 6, 3, BROWN)


def draw_player_fish(surf, frame=0, facing=1):
    """捕捞动作"""
    hflip = -1 if facing < 0 else 1
    fx = lambda x: SPRITE_W//2 + (x - SPRITE_W//2) * hflip
    raise_arm = frame % 2 * 2

    # 头发
    rect(surf, fx(13), 3, 7, 4, HAIR)
    # 头
    rect(surf, fx(12), 7, 8, 8, SKIN_L)
    px(surf, fx(14), 11, BLACK)
    px(surf, fx(17), 11, BLACK)
    # 身体
    rect(surf, fx(12), 15, 8, 10, c(160, 100, 50))
    # 举起的臂 + 鱼竿
    rect(surf, fx(22), 13 - raise_arm, 3, 8, SKIN_M)
    rect(surf, fx(24), 5 - raise_arm, 1, 16, TAN)   # 鱼竿
    rect(surf, fx(25), 18 - raise_arm, 1, 5, CYAN)  # 鱼线
    # 另一只臂
    rect(surf, fx(9), 20, 3, 7, SKIN_M)
    # 腿
    rect(surf, fx(12), 25, 4, 12, TAN)
    rect(surf, fx(17), 25, 4, 12, TAN)
    rect(surf, fx(11), 36, 6, 3, BROWN)
    rect(surf, fx(16), 36, 6, 3, BROWN)


def draw_player_hurt(surf, frame=0, facing=1):
    """受伤帧"""
    hflip = -1 if facing < 0 else 1
    fx = lambda x: SPRITE_W//2 + (x - SPRITE_W//2) * hflip
    knockback = frame * 2

    # 头发
    rect(surf, fx(13) - knockback, 3, 7, 4, HAIR)
    # 头
    rect(surf, fx(12) - knockback, 7, 8, 8, SKIN_L)
    # 受伤表情 (X_X)
    px(surf, fx(14) - knockback, 11, RED)
    px(surf, fx(15) - knockback, 12, RED)
    px(surf, fx(17) - knockback, 11, RED)
    px(surf, fx(18) - knockback, 12, RED)
    # 身体 (后仰)
    rect(surf, fx(12) - knockback, 15, 8, 10, c(160, 100, 50))
    # 手臂张开
    rect(surf, fx(8) - knockback,  17, 3, 7, SKIN_M)
    rect(surf, fx(23) - knockback, 17, 3, 7, SKIN_M)
    # 汗滴
    rect(surf, fx(11) - knockback, 5, 1, 2, BLUE)
    rect(surf, fx(20) - knockback, 4, 1, 2, BLUE)
    # 腿
    rect(surf, fx(12) - knockback, 25, 4, 12, TAN)
    rect(surf, fx(17) - knockback, 25, 4, 12, TAN)
    rect(surf, fx(11) - knockback, 36, 6, 3, BROWN)
    rect(surf, fx(16) - knockback, 36, 6, 3, BROWN)


def generate_player():
    """生成主角精灵图：待机/站立/行走/捕捞/受伤"""
    idle_frame = make_frame(lambda s: draw_player_idle(s, 0, 1))
    walk_frames = [make_frame(lambda s, fi=i: draw_player_walk(s, fi, 1)) for i in range(4)]
    fish_frames = [make_frame(lambda s, fi=i: draw_player_fish(s, fi, 1)) for i in range(2)]
    hurt_frames = [make_frame(lambda s, fi=i: draw_player_hurt(s, fi, 1)) for i in range(2)]
    idle_l_frames = [make_frame(lambda s: draw_player_idle(s, 0, -1))]
    walk_l_frames = [make_frame(lambda s, fi=i: draw_player_walk(s, fi, -1)) for i in range(4)]
    frames = [
        [idle_frame],
        walk_frames,
        fish_frames,
        hurt_frames,
        idle_l_frames,
        walk_l_frames,
    ]
    return SpriteSheet("player", frames, ["idle","walk","fish","hurt","idle_l","walk_l"])


# ══════════════════════════════════════════════════════
#  怪物们
# ══════════════════════════════════════════════════════

def draw_crab(surf, frame=0):
    """海蟹 - 红色小螃蟹"""
    # 身体
    rect(surf, 9, 22, 14, 10, RED)
    rect(surf, 10, 20, 12, 3, RED)
    rect(surf, 8, 24, 16, 6, DARK_R)
    # 眼睛
    px(surf, 12, 18, BLACK); px(surf, 18, 18, BLACK)
    px(surf, 12, 17, WHITE); px(surf, 18, 17, WHITE)
    # 螯
    claw_off = 1 if frame % 2 == 0 else -1
    rect(surf, 3,  22 + claw_off, 6, 4, RED)
    rect(surf, 23, 22 - claw_off, 6, 4, RED)
    rect(surf, 2,  21 + claw_off, 3, 3, DARK_R)
    rect(surf, 27, 21 - claw_off, 3, 3, DARK_R)
    # 腿
    for i, ox in enumerate([-3, -1, 1, 3]):
        lx = 11 + i * 3
        rect(surf, lx, 32, 2, 5, DARK_R)
        rect(surf, lx + ox, 36, 2, 3, RED)


def draw_shark(surf, frame=0):
    """鲨鱼 - 大型敌人"""
    # 身体
    for y in range(15, 30):
        w = 6 if y < 18 or y > 27 else 14 + (y-18)//2
        rect(surf, 16 - w//2, y, w, 1, DARK_B)
    rect(surf, 10, 18, 16, 10, BLUE)
    rect(surf, 8,  22, 6, 5, DARK_B)  # 头
    # 眼睛
    px(surf, 9, 22, BLACK); px(surf, 9, 22, WHITE)
    # 鳍
    fin_y = 14 - (frame % 2)
    rect(surf, 18, fin_y, 4, 6, DARK_B)
    # 尾巴
    tail_x = 26 + (frame % 2)
    rect(surf, tail_x, 20, 5, 3, DARK_B)
    rect(surf, tail_x + 3, 18, 3, 3, DARK_B)
    rect(surf, tail_x + 3, 25, 3, 3, DARK_B)
    # 牙齿
    px(surf, 6, 23, WHITE); px(surf, 7, 23, WHITE); px(surf, 8, 24, WHITE)
    # 腹部
    rect(surf, 12, 26, 10, 3, TAN)


def draw_octopus(surf, frame=0):
    """巨型章鱼"""
    # 头
    ellipse(surf, 16, 18, 10, 9, PURPLE)
    ellipse(surf, 16, 17, 8, 7, c(170, 100, 200))
    # 眼睛
    px(surf, 12, 16, WHITE); px(surf, 19, 16, WHITE)
    px(surf, 12, 16, BLACK); px(surf, 19, 16, BLACK)
    # 吸盘
    for i in range(4):
        px(surf, 13 + i * 2, 21, c(200, 150, 220))
    # 触手
    wave = frame % 2
    for i, ox in enumerate([-7, -4, 0, 4, 7]):
        tx = 16 + ox
        ty = 26
        rect(surf, tx, ty, 2, 4 + wave, PURPLE)
        rect(surf, tx + (i%2)*1, ty + 4, 2, 5 - wave, c(180, 100, 200))


def draw_sea_snake(surf, frame=0):
    """海蛇 - 细长"""
    wave = frame % 4
    # 身体波浪
    for i in range(10):
        wx = 8 + i * 2
        wy = 20 + (wave - i) % 3
        rect(surf, wx, wy, 3, 3, TEAL)
        rect(surf, wx+1, wy+1, 1, 1, c(100, 200, 200))
    # 头
    hx = 28 + (wave % 2)
    rect(surf, hx, 18, 4, 5, TEAL)
    rect(surf, hx, 17, 3, 3, DARK_G)
    # 眼睛
    px(surf, hx+2, 19, RED)
    # 舌头
    px(surf, hx+4, 20, PINK); px(surf, hx+5, 20, PINK)


def draw_dragon(surf, frame=0):
    """海龙王 - Boss"""
    # 身体
    rect(surf, 6, 16, 20, 16, c(80, 40, 160))
    rect(surf, 8, 14, 16, 4, c(60, 20, 140))
    # 鳞片
    for y in range(18, 32, 3):
        for x in range(8, 26, 4):
            px(surf, x, y, c(120, 60, 200))
    # 头
    rect(surf, 24, 12, 8, 10, c(60, 20, 140))
    rect(surf, 28, 8, 6, 6, c(80, 40, 160))   # 冠
    # 角
    rect(surf, 30, 5, 2, 5, GOLD)
    rect(surf, 27, 6, 2, 5, GOLD)
    # 眼睛
    px(surf, 26, 14, RED); px(surf, 29, 14, RED)
    # 嘴
    px(surf, 30, 19, BLACK); px(surf, 31, 19, BLACK)
    # 三叉戟
    tine_x = 32 + (frame % 2)
    rect(surf, tine_x, 5, 1, 25, TAN)
    rect(surf, tine_x-2, 5, 1, 5, GOLD)
    rect(surf, tine_x+2, 5, 1, 5, GOLD)
    # 鳍/尾
    rect(surf, 4, 20, 3, 4, c(60, 20, 140))
    rect(surf, 2, 18, 4, 3, c(60, 20, 140))
    # 爪
    rect(surf, 8, 32, 3, 4, c(80, 40, 160))
    rect(surf, 22, 32, 3, 4, c(80, 40, 160))


def draw_attack_effect(surf, frame=0):
    """攻击特效 - 闪光"""
    # 白色闪光中心
    rect(surf, 13, 16, 6, 8, YELLOW)
    rect(surf, 12, 17, 8, 6, WHITE)
    rect(surf, 10, 18, 12, 4, YELLOW)
    # 光线
    rays = [(15, 10), (17, 8), (19, 10), (20, 12), (19, 14), (17, 16)]
    for rx, ry in rays:
        px(surf, rx + (frame%2), ry - (frame%2), YELLOW)


def draw_hurt_effect(surf, frame=0):
    """受伤特效 - 红色X"""
    # 红色X
    for i in range(8):
        px(surf, 10+i, 16+i, RED)
        px(surf, 22-i, 16+i, RED)
    # 星星
    px(surf, 16, 12, WHITE)
    px(surf, 14, 14, WHITE)
    px(surf, 18, 14, WHITE)
    px(surf, 16, 16, WHITE)


def draw_victory_effect(surf, frame=0):
    """胜利 - 星星"""
    colors = [GOLD, YELLOW, WHITE, ORANGE]
    # 星星形状
    cx, cy = 16, 20
    for dx, dy in [(-4,-2),(4,-2),(-4,2),(4,2),(-2,-4),(2,-4),(-2,4),(2,4),(0,0)]:
        px(surf, cx+dx+(frame%2), cy+dy, colors[frame%4])
    px(surf, cx, cy-5, GOLD)
    px(surf, cx-5, cy, GOLD)
    px(surf, cx+5, cy, GOLD)
    px(surf, cx, cy+5, GOLD)


def generate_monsters():
    """生成所有怪物精灵图"""
    enemy_frames = [
        # 海蟹
        [make_frame(lambda s, i=i: draw_crab(s, i)) for i in range(2)],
        # 鲨鱼
        [make_frame(lambda s, i=i: draw_shark(s, i)) for i in range(2)],
        # 巨型章鱼
        [make_frame(lambda s, i=i: draw_octopus(s, i)) for i in range(2)],
        # 海蛇
        [make_frame(lambda s, i=i: draw_sea_snake(s, i)) for i in range(4)],
        # 海龙王
        [make_frame(lambda s, i=i: draw_dragon(s, i)) for i in range(2)],
    ]
    SpriteSheet("enemies", enemy_frames,
                ["crab","shark","octopus","sea_snake","dragon"]).save()

    effects = [
        [make_frame(lambda s, i=i: draw_attack_effect(s, i)) for i in range(2)],
        [make_frame(lambda s, i=i: draw_hurt_effect(s, i)) for i in range(2)],
        [make_frame(lambda s, i=i: draw_victory_effect(s, i)) for i in range(4)],
    ]
    SpriteSheet("effects", effects, ["attack","hurt","victory"]).save()


# ══════════════════════════════════════════════════════
#  岛屿装饰物
# ══════════════════════════════════════════════════════

def draw_boat(surf):
    """小木筏"""
    # 木板
    rect(surf, 4, 26, 24, 4, TAN)
    rect(surf, 6, 24, 20, 3, BROWN)
    # 绳子
    rect(surf, 14, 16, 2, 10, YELLOW)
    # 帆
    rect(surf, 16, 10, 8, 8, c(230, 200, 150))
    rect(surf, 15, 10, 2, 9, BROWN)


def draw_campfire(surf, frame=0):
    """篝火"""
    # 木头
    rect(surf, 8, 30, 16, 4, BROWN)
    rect(surf, 6, 32, 20, 3, c(100, 60, 30))
    # 火焰
    h = 8 + frame % 3
    rect(surf, 13, 32 - h, 6, h, ORANGE)
    rect(surf, 14, 32 - h + 2, 4, h - 2, YELLOW)
    rect(surf, 15, 32 - h + 4, 2, h - 4, WHITE)
    # 火星
    for i in range(3):
        sx = 10 + i * 5 + (frame % 2)
        sy = 28 - (frame % 3) * 2
        px(surf, sx, sy, ORANGE)


def draw_treasure(surf):
    """宝箱"""
    rect(surf, 8, 24, 16, 10, BROWN)
    rect(surf, 8, 24, 16, 3, GOLD)
    rect(surf, 14, 25, 4, 6, YELLOW)
    px(surf, 16, 27, GOLD)


def draw_dead_tree(surf):
    """枯树"""
    rect(surf, 15, 8, 3, 30, BROWN)
    rect(surf, 8, 12, 4, 2, BROWN)
    rect(surf, 20, 14, 5, 2, BROWN)
    rect(surf, 6, 8, 3, 5, BROWN)


def draw_footprints(surf, frame=0):
    """脚印"""
    for i in range(4):
        fx = 6 + i * 8
        fy = 20 + (i % 2) * 5 + (frame % 2)
        rect(surf, fx, fy, 3, 5, TAN)
        rect(surf, fx+4, fy+2, 3, 5, TAN)


def draw_fish_splash(surf, frame=0):
    """鱼跃出水"""
    # 鱼身
    rect(surf, 8, 20, 14, 6, BLUE)
    rect(surf, 20, 21, 5, 4, DARK_B)
    # 水花
    for i in range(5):
        sx = 10 + i * 4 + (frame % 3)
        sy = 16 - abs(i-2) * 2
        px(surf, sx, sy, CYAN)
        px(surf, sx+1, sy-1, CYAN)


def generate_decorations():
    """生成装饰物精灵图"""
    deco_frames = [
        [make_frame(draw_boat)],
        [make_frame(lambda s, i=i: draw_campfire(s, i)) for i in range(3)],
        [make_frame(draw_treasure)],
        [make_frame(draw_dead_tree)],
        [make_frame(lambda s, i=i: draw_footprints(s, i)) for i in range(2)],
        [make_frame(lambda s, i=i: draw_fish_splash(s, i)) for i in range(3)],
    ]
    SpriteSheet("decorations", deco_frames,
                ["boat","campfire","treasure","tree","footprint","fish_splash"]).save()


# ══════════════════════════════════════════════════════
#  主程序
# ══════════════════════════════════════════════════════
def main():
    print("Generating sprites...")
    os.makedirs(OUT_DIR, exist_ok=True)

    print("\n  [主角]")
    generate_player().save()

    print("\n  [怪物]")
    generate_monsters()

    print("\n  [装饰物]")
    generate_decorations()

    # 生成小缩略图预览
    preview = pygame.Surface((32 * 3, 40 * 12), pygame.SRCALPHA)
    preview.fill((30, 30, 50))

    # Row 1: Player idle
    idle = make_frame(lambda s: draw_player_idle(s, 0, 1))
    preview.blit(pygame.transform.scale(idle, (96, 120)), (0, 0))

    # Row 2: Enemies
    crab = make_frame(lambda s: draw_crab(s, 0))
    shark = make_frame(lambda s: draw_shark(s, 0))
    octo = make_frame(lambda s: draw_octopus(s, 0))
    snake = make_frame(lambda s: draw_sea_snake(s, 0))
    dragon = make_frame(lambda s: draw_dragon(s, 0))

    enemies = [crab, shark, octo, snake, dragon]
    for i, e in enumerate(enemies):
        preview.blit(pygame.transform.scale(e, (96, 120)), (i * 96, 120))

    pygame.image.save(preview, os.path.join(OUT_DIR, "preview.png"))
    print(f"\n  ✓ preview.png")

    print(f"\nAll sprites saved to: {OUT_DIR}")
    print(f"Files: {sorted(os.listdir(OUT_DIR))}")

main()
pygame.quit()
