"""Sprite system: loads PNG sheets and manages animation playback."""

import pygame, os
from config import SW, SH

# Root directory of the game (parent of the sprites/ folder)
GAME_ROOT = os.path.dirname(__file__)

class SpriteSheet:
    """A single sprite sheet with named animation rows."""

    def __init__(self, filename, frame_w=32, frame_h=40, scale=3):
        self.path = os.path.join(GAME_ROOT, "sprites", filename)
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.scale = scale
        self.display_w = frame_w * scale
        self.display_h = frame_h * scale
        try:
            raw = pygame.image.load(self.path).convert_alpha()
            self.sheet = pygame.transform.scale(
                raw,
                (raw.get_width() * scale, raw.get_height() * scale)
            )
        except Exception as e:
            print(f"WARNING: Could not load sprite sheet {self.path}: {e}")
            self.sheet = pygame.Surface((1, 1), pygame.SRCALPHA)

        # Parse: each row is one animation
        rows = self.sheet.get_height() // self.display_h
        cols = self.sheet.get_width() // self.display_w
        self.row_count = rows
        self.col_count = cols

    def get_frame(self, row, col=0) -> pygame.Surface:
        """Extract a single frame surface."""
        x = col * self.display_w
        y = row * self.display_h
        frame = pygame.Surface((self.display_w, self.display_h), pygame.SRCALPHA)
        frame.blit(self.sheet, (0, 0), area=(x, y, self.display_w, self.display_h))
        return frame


class AnimState:
    """Manages animation state for a single entity (player/enemy)."""

    def __init__(self, sheet: SpriteSheet, row: int = 0,
                 fps: int = 6, loop: bool = True):
        self.sheet = sheet
        self.row = row
        self.fps = fps
        self.loop = loop
        self.frame = 0
        self.timer = 0.0
        self.done = False

    @property
    def current_frame(self) -> pygame.Surface:
        col = min(int(self.frame), self.sheet.col_count - 1)
        return self.sheet.get_frame(self.row, col)

    def update(self, dt: float):
        """Advance animation. Returns True when one full cycle completes."""
        if self.done and not self.loop:
            return False
        self.timer += dt
        interval = 1.0 / self.fps if self.fps > 0 else 1.0
        if self.timer >= interval:
            self.timer -= interval
            prev = int(self.frame)
            self.frame = (self.frame + 1) % self.sheet.col_count
            if self.loop or self.frame != 0:
                pass
            elif not self.loop and self.frame == 0 and prev == self.sheet.col_count - 1:
                self.done = True
                return True
        return False

    def set_row(self, row: int, restart: bool = True):
        """Switch to a different animation row (e.g., idle→walk)."""
        if self.row != row and 0 <= row < self.sheet.row_count:
            self.row = row
            if restart:
                self.frame = 0
                self.timer = 0.0
                self.done = False

    def reset(self):
        self.frame = 0; self.timer = 0.0; self.done = False


# ─── Singleton sprite references ──────────────────────────────────────────────

def load_all_sprites():
    """Load all sprite sheets and return dict of SpriteSheet."""
    sheets = {}
    for name, fname, fw, fh, sc in [
        ("player",      "player.png",       32, 40, 3),
        ("enemies",     "enemies.png",      32, 40, 3),
        ("effects",     "effects.png",      32, 40, 3),
        ("decorations", "decorations.png",  32, 40, 3),
    ]:
        sheets[name] = SpriteSheet(fname, fw, fh, sc)
    return sheets

# Lazy-loaded singleton
_sheets = None

def get_sprites():
    global _sheets
    if _sheets is None:
        _sheets = load_all_sprites()
    return _sheets


# ─── Player animation row map ───────────────────────────────────────────────
# player.png rows: 0=idle_right, 1=walk_right, 2=fish, 3=hurt, 4=idle_left, 5=walk_left

PLAYER_ROWS = {
    "idle_right": 0,
    "idle_left":  4,
    "walk_right":  1,
    "walk_left":  5,
    "fish":       2,
    "hurt":       3,
}

# enemy.png rows: 0=crab, 1=shark, 2=octopus, 3=sea_snake, 4=dragon
ENEMY_ROWS = {
    "海蟹":     0,
    "鲨鱼":     1,
    "巨型章鱼": 2,
    "海蛇":     3,
    "海龙王":   4,
}

# effects.png rows: 0=attack, 1=hurt, 2=victory
EFFECT_ROWS = {
    "attack":  0,
    "hurt":    1,
    "victory": 2,
}

# decorations.png rows: 0=boat, 1=campfire, 2=treasure, 3=tree, 4=footprint, 5=fish_splash
DECO_ROWS = {
    "boat":       0,
    "campfire":  1,
    "treasure":  2,
    "tree":      3,
    "footprint": 4,
    "fish_splash": 5,
}
