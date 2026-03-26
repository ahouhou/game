"""Sprite system: loads PNG sheets and manages animation playback.

Frame layouts are derived from auto-scanning pixel data of the generated sheets.
Key insight: the generate_sprites.py puts one animation per logical group of
consecutive columns, but due to the SCALE layout, data starts at row 1 (row 0
is always blank).  We scan each row and group non-empty columns into frames.
"""

import pygame, os

GAME_ROOT = os.path.dirname(__file__)

# ─────────────────────────────────────────────────────────────────────────────
# Frame layout tables  {logical_row: [col_indices_of_active_frames]}
# These were derived by scanning the actual generated PNG files.
# Columns 0-5 are used for 3 logical frames (each frame uses 2 pixel cols).
# ─────────────────────────────────────────────────────────────────────────────

# enemies.png (15 rows × 12 cols, 96×120 px/frame, scale=3)
# row 0=blank, row 1=海蟹, row 2=鲨鱼, row 4=巨型章鱼,
# row 8=海蛇, row 13=海龙王
ENEMY_FRAMES = {
    1: [0, 1, 2, 3, 4, 5],   # 海蟹 idle  (3 animation frames × 2 pixel cols)
    2: [0, 1, 2, 3, 4, 5],   # 鲨鱼 idle  (3 frames)
    4: [0, 1, 2, 3, 4, 5],   # 巨型章鱼   (3 frames)
    8: [0, 1, 2, 3, 4, 5],   # 海蛇 idle  (3 frames)
   13: [0, 1, 2, 3, 4, 5],   # 海龙王     (3 frames)
}

ENEMY_ROWS = {
    "海蟹":     1,
    "鲨鱼":     2,
    "巨型章鱼": 4,
    "海蛇":     8,
    "海龙王":  13,
}

# player.png (18 rows × 12 cols) — starts at row 0 (no blank header)
PLAYER_FRAMES = {
    0: [1],           # idle_right
    1: [1, 2],        # walk_right  (2 pixel cols = 1 logical frame)
    2: [1, 2],        # fish
    3: [1],           # hurt
    4: [1, 2, 3],    # idle_left
    5: [1],           # walk_left
}

PLAYER_ROWS = {
    "idle_right": 0, "walk_right": 1, "fish": 2,
    "hurt": 3, "idle_left": 4, "walk_left": 5,
}

# effects.png (9 rows × 12 cols)
EFFECT_FRAMES = {
    0: [1, 4, 5],     # attack spark
    1: [0, 1, 2, 3, 4, 5],  # hurt
    4: [0, 1, 2, 3, 4, 5],  # pickup
    7: [1, 2, 4, 5, 7, 8],  # build_complete
}

EFFECT_ROWS = {
    "attack": 0, "hurt": 1, "pickup": 4, "build_complete": 7,
}

# decorations.png (18 rows × 9 cols)
DECO_FRAMES = {
    0: [1, 2],           # boat (2 frames)
    1: [0, 1, 2],        # campfire
    2: [0, 1, 2],        # treasure chest
    5: [0, 1, 2, 3, 4, 5],  # fish_splash
   13: [0, 1, 2, 3],    # palm_tree
   16: [0, 1, 2, 3],    # chest_open
}

DECO_ROWS = {
    "boat": 0, "campfire": 1, "treasure": 2,
    "fish_splash": 5, "palm_tree": 13, "chest_open": 16,
}

FRAME_MAPS = {
    "player":      PLAYER_FRAMES,
    "enemies":     ENEMY_FRAMES,
    "effects":     EFFECT_FRAMES,
    "decorations": DECO_FRAMES,
}


# ─────────────────────────────────────────────────────────────────────────────
# SpriteSheet
# ─────────────────────────────────────────────────────────────────────────────

class SpriteSheet:
    def __init__(self, filename, frame_w=32, frame_h=40, scale=3):
        self._key = filename.rsplit(".", 1)[0]   # short name for FRAME_MAPS
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.scale = scale
        self.dw = frame_w * scale
        self.dh = frame_h * scale
        self.path = os.path.join(GAME_ROOT, "sprites", filename)
        try:
            raw = pygame.image.load(self.path).convert_alpha()
            W, H = raw.get_width(), raw.get_height()
            self.sheet = pygame.transform.scale(raw, (W * scale, H * scale))
        except Exception as e:
            print(f"WARNING: Could not load {self.path}: {e}")
            self.sheet = pygame.Surface((1, 1), pygame.SRCALPHA)

    @property
    def cols(self) -> int:
        return self.sheet.get_width() // self.dw

    @property
    def rows(self) -> int:
        return self.sheet.get_height() // self.dh

    def get_frame(self, row: int, col: int) -> pygame.Surface:
        surf = pygame.Surface((self.dw, self.dh), pygame.SRCALPHA)
        surf.blit(self.sheet, (0, 0),
                  area=(col * self.dw, row * self.dh, self.dw, self.dh))
        return surf


# ─────────────────────────────────────────────────────────────────────────────
# AnimState
# ─────────────────────────────────────────────────────────────────────────────

class AnimState:
    def __init__(self, sheet: SpriteSheet, row: int = 0,
                 frames: list = None, fps: int = 6, loop: bool = True):
        self.sheet = sheet
        self.row = row
        self.fps = fps
        self.loop = loop
        self.timer = 0.0
        self.done = False
        fm = FRAME_MAPS.get(sheet._key, {})
        self.frames = frames if frames is not None else fm.get(row, [1])
        self.fi = 0

    @property
    def current_frame(self) -> pygame.Surface:
        col = self.frames[min(self.fi, len(self.frames) - 1)]
        return self.sheet.get_frame(self.row, col)

    def update(self, dt: float):
        if self.done:
            return False
        self.timer += dt
        if self.timer >= 1.0 / max(self.fps, 1):
            self.timer -= 1.0 / self.fps
            prev = self.fi
            self.fi = (self.fi + 1) % len(self.frames)
            if not self.loop and self.fi == 0 and prev == len(self.frames) - 1:
                self.done = True
                return True
        return False

    def set_row(self, row: int, restart: bool = True):
        if self.row != row:
            self.row = row
            fm = FRAME_MAPS.get(self.sheet._key, {})
            self.frames = fm.get(row, [1])
            if restart:
                self.fi = 0
                self.timer = 0.0
                self.done = False

    def reset(self):
        self.fi = 0; self.timer = 0.0; self.done = False


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_sheets = None

def load_all_sprites():
    return {
        "player":      SpriteSheet("player.png",       32, 40, 3),
        "enemies":     SpriteSheet("enemies.png",      32, 40, 3),
        "effects":     SpriteSheet("effects.png",      32, 40, 3),
        "decorations": SpriteSheet("decorations.png",  32, 40, 3),
    }

def get_sprites():
    global _sheets
    if _sheets is None:
        _sheets = load_all_sprites()
    return _sheets
