"""Screen size, colors, and game constants."""

# --- Screen ---
SW, SH = 1400, 900
FPS = 60

# --- Colors (ALL tuples, NEVER strings) ---
WHITE       = (255, 255, 255)
BLACK       = (0, 0, 0)
C_SAND      = (237, 201, 130)
C_OCEAN     = (30, 120, 200)
C_OCEAN_D   = (15, 70, 150)
C_GRASS     = (56, 142, 60)
C_HEALTH    = (220, 60, 60)
C_HUNGER    = (230, 140, 30)
C_ENERGY    = (240, 220, 60)
C_SUCCESS   = (76, 175, 80)
C_WARNING   = (230, 80, 40)
C_BROWN     = (139, 90, 43)
C_STONE     = (140, 140, 140)
C_GOLD      = (255, 200, 50)
C_DARK      = (18, 22, 36)
C_PANEL     = (12, 16, 30)
C_BORDER    = (60, 70, 100)
C_STORM     = (90, 110, 130)
C_FOG       = (140, 140, 155, 70)
C_TEXT_DIM  = (130, 130, 140)

# --- Game settings ---
DAILY_HUNGER_LOSS = 12
STARVATION_DAMAGE = 15
DISASTER_CHANCE = 0.30        # 30% per day
QUEST_SPAWN_CHANCE = 0.35     # 35% per day
DRIFT_BOTTLE_CHANCE = 0.08    # 8% after day 2
ACTION_POINTS = 3
SAVE_SLOTS = 3
