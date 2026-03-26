"""UI helper: Button widget + progress bar + panel."""

import pygame
from config import C_TEXT_DIM, C_BORDER

# Need fonts globally; set by Game.__init__
_fonts = {}

def init_fonts(font_names=None):
    """Initialize font dict. Must call before rendering. Returns dict."""
    global _fonts
    # macOS Chinese font (lowercase from pygame.font.get_fonts())
    CJK_FONTS = ["stheitimedium", "stheitilight", "pingfangsc", "notosanscjk_sc"]
    FALLBACK  = ["arial", "liberationsans", "ubuntu", "dejavusans", None]
    sizes = [("xs",14),("sm",18),("md",24),("lg",36),("xl",48)]
    for sz, pt in sizes:
        for name in (font_names or CJK_FONTS + FALLBACK):
            try:
                f = pygame.font.SysFont(name, pt)
                t = f.render("荒", True, (255,255,255))
                if t.get_size()[0] > 10:   # Chinese renders to wide surface
                    _fonts[sz] = f
                    break
            except Exception:
                pass
        if sz not in _fonts:
            _fonts[sz] = pygame.font.Font(None, pt)

def font(size="sm"):
    return _fonts.get(size, _fonts["sm"])


class Button:
    """Self-contained clickable button. Single source of truth for rect."""
    def __init__(self, x, y, w, h, text, bg_color, text_color=(255,255,255), enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg = bg_color
        self.fg = text_color
        self.enabled = enabled

    def draw(self, surface, mouse_pos=None):
        if not self.enabled:
            bg = tuple(c // 2 for c in self.bg)
            fg = (100, 100, 100)
        else:
            bg = self.bg
            fg = self.fg
        # hover highlight
        if mouse_pos and self.rect.collidepoint(mouse_pos) and self.enabled:
            bg = tuple(min(255, c + 30) for c in bg)
        # draw
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        # top highlight
        hi = pygame.Surface((self.rect.w - 4, min(8, self.rect.h // 3)), pygame.SRCALPHA)
        hi.fill((*[min(255, c + 50) for c in bg], 80))
        surface.blit(hi, (self.rect.x + 2, self.rect.y + 2))
        # border
        pygame.draw.rect(surface, (255, 255, 255) if self.enabled else (60,60,60),
                         self.rect, 1, border_radius=8)
        # text
        t = font("sm").render(self.text, True, fg)
        surface.blit(t, t.get_rect(center=self.rect.center))

    def clicked(self, pos) -> bool:
        return self.enabled and self.rect.collidepoint(pos)


def draw_bar(surface, x, y, w, h, value, max_value, color):
    """Horizontal progress bar."""
    ratio = max(0, min(1, value / max_value)) if max_value > 0 else 0
    # bg
    pygame.draw.rect(surface, (30, 30, 40), (x, y, w, h), border_radius=4)
    # fill
    if ratio > 0:
        fill_w = int(w * ratio)
        pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=4)
    # border
    pygame.draw.rect(surface, C_BORDER, (x, y, w, h), 1, border_radius=4)


def draw_panel(surface, x, y, w, h, title=None, border_color=C_BORDER):
    """Dark semi-transparent panel."""
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((10, 14, 28, 220))
    surface.blit(panel, (x, y))
    pygame.draw.rect(surface, border_color, (x, y, w, h), 2, border_radius=12)
    if title:
        t = font("lg").render(title, True, (255, 200, 100))
        surface.blit(t, (x + 20, y + 15))
        pygame.draw.line(surface, border_color, (x + 20, y + 58), (x + w - 20, y + 58), 1)


def draw_text_center(surface, text, y, color=(255,255,255), size="md"):
    t = font(size).render(text, True, color)
    surface.blit(t, t.get_rect(center=(700, y)))
    return t.get_rect(center=(700, y))
