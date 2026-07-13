"""
ui.py — Custom UI components for the sorting visualizer.

Provides modern dark-themed buttons, sliders, and panels rendered with pygame.
"""

import pygame

# ─── Color Palette ───────────────────────────────────────────────────────────
BG_DARK = (12, 12, 30)
BG_PANEL = (20, 20, 45)
BG_PANEL_BORDER = (45, 45, 80)
TEXT_PRIMARY = (230, 230, 245)
TEXT_SECONDARY = (150, 150, 175)
TEXT_DIM = (100, 100, 130)
ACCENT_CYAN = (0, 210, 255)
ACCENT_MAGENTA = (255, 0, 180)
ACCENT_GREEN = (0, 255, 140)
ACCENT_RED = (255, 60, 80)
ACCENT_ORANGE = (255, 160, 40)
BTN_IDLE = (35, 35, 65)
BTN_HOVER = (50, 50, 85)
BTN_ACTIVE = (25, 100, 160)
BTN_DISABLED = (25, 25, 45)
SLIDER_TRACK = (40, 40, 70)
SLIDER_FILL = (0, 160, 220)
SLIDER_KNOB = (220, 220, 240)
DIVIDER = (40, 40, 70)


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Linearly interpolate between two RGB colors."""
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=None):
    """Draw a rounded rectangle."""
    r = pygame.Rect(rect)
    if border > 0 and border_color:
        pygame.draw.rect(surface, border_color, r, border_radius=radius)
        inner = r.inflate(-border * 2, -border * 2)
        pygame.draw.rect(surface, color, inner, border_radius=max(0, radius - border))
    else:
        pygame.draw.rect(surface, color, r, border_radius=radius)


class Font:
    """Font manager singleton."""
    _fonts: dict = {}

    @classmethod
    def get(cls, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in cls._fonts:
            font = pygame.font.SysFont("Segoe UI", size, bold=bold)
            if font is None:
                font = pygame.font.SysFont("Arial", size, bold=bold)
            cls._fonts[key] = font
        return cls._fonts[key]


class Button:
    """Modern styled button with hover and active states."""

    def __init__(self, x, y, w, h, text, font_size=14, accent=None, toggle=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font_size = font_size
        self.accent = accent
        self.toggle = toggle

        self.hovered = False
        self.pressed = False
        self.active = False  # For toggle buttons
        self.enabled = True
        self._click_anim = 0.0

    def update(self, mouse_pos, mouse_pressed, events):
        """Update button state. Returns True if clicked this frame."""
        clicked = False
        self.hovered = self.rect.collidepoint(mouse_pos) and self.enabled

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered:
                    self.pressed = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.pressed and self.hovered:
                    clicked = True
                    if self.toggle:
                        self.active = not self.active
                    self._click_anim = 1.0
                self.pressed = False

        if self._click_anim > 0:
            self._click_anim = max(0, self._click_anim - 0.08)

        return clicked

    def draw(self, surface):
        """Render the button."""
        if not self.enabled:
            bg = BTN_DISABLED
            text_color = TEXT_DIM
        elif self.active and self.toggle:
            bg = self.accent or BTN_ACTIVE
            text_color = TEXT_PRIMARY
        elif self.pressed:
            bg = self.accent or BTN_ACTIVE
            text_color = TEXT_PRIMARY
        elif self.hovered:
            bg = BTN_HOVER
            text_color = TEXT_PRIMARY
        else:
            bg = BTN_IDLE
            text_color = TEXT_SECONDARY

        # Draw button background
        draw_rounded_rect(surface, bg, self.rect, radius=6)

        # Active indicator line at bottom
        if self.active and self.toggle:
            indicator_color = ACCENT_CYAN if not self.accent else self.accent
            indicator_rect = pygame.Rect(
                self.rect.x + 4, self.rect.bottom - 3, self.rect.width - 8, 2
            )
            pygame.draw.rect(surface, indicator_color, indicator_rect, border_radius=1)

        # Hover glow border
        if self.hovered and self.enabled and not self.pressed:
            glow_color = (*ACCENT_CYAN[:3],) if not self.accent else self.accent
            pygame.draw.rect(surface, glow_color, self.rect, width=1, border_radius=6)

        # Text
        font = Font.get(self.font_size, bold=self.active)
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Slider:
    """Horizontal slider with label and value display."""

    def __init__(self, x, y, w, label, min_val, max_val, value, step=1,
                 value_format=None, font_size=12):
        self.x = x
        self.y = y
        self.w = w
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self._value = value
        self.step = step
        self.value_format = value_format or str
        self.font_size = font_size

        self.track_rect = pygame.Rect(x, y + 22, w, 6)
        self.knob_radius = 8
        self.dragging = False
        self.hovered = False
        self.enabled = True

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = max(self.min_val, min(self.max_val, v))
        # Snap to step
        if self.step >= 1:
            self._value = round(self._value / self.step) * self.step

    @property
    def knob_x(self):
        ratio = (self._value - self.min_val) / max(1, self.max_val - self.min_val)
        return self.x + int(ratio * self.w)

    def update(self, mouse_pos, mouse_pressed, events):
        """Update slider state. Returns True if value changed."""
        old_value = self._value
        knob_center = (self.knob_x, self.track_rect.centery)
        knob_rect = pygame.Rect(
            knob_center[0] - self.knob_radius,
            knob_center[1] - self.knob_radius,
            self.knob_radius * 2,
            self.knob_radius * 2,
        )
        expanded_track = self.track_rect.inflate(0, 16)

        self.hovered = (knob_rect.collidepoint(mouse_pos) or
                        expanded_track.collidepoint(mouse_pos))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered and self.enabled:
                    self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False

        if self.dragging and self.enabled:
            ratio = (mouse_pos[0] - self.x) / max(1, self.w)
            ratio = max(0.0, min(1.0, ratio))
            self.value = self.min_val + ratio * (self.max_val - self.min_val)

        return self._value != old_value

    def draw(self, surface):
        """Render the slider."""
        # Label
        font = Font.get(self.font_size)
        label_surf = font.render(self.label, True, TEXT_SECONDARY)
        surface.blit(label_surf, (self.x, self.y))

        # Value text
        val_text = self.value_format(self._value)
        val_surf = font.render(val_text, True, ACCENT_CYAN)
        surface.blit(val_surf, (self.x + self.w - val_surf.get_width(), self.y))

        # Track background
        pygame.draw.rect(surface, SLIDER_TRACK, self.track_rect, border_radius=3)

        # Filled portion
        fill_width = self.knob_x - self.x
        if fill_width > 0:
            fill_rect = pygame.Rect(self.x, self.track_rect.y, fill_width, 6)
            pygame.draw.rect(surface, SLIDER_FILL, fill_rect, border_radius=3)

        # Knob
        knob_color = ACCENT_CYAN if (self.dragging or self.hovered) else SLIDER_KNOB
        pygame.draw.circle(
            surface, knob_color,
            (self.knob_x, self.track_rect.centery),
            self.knob_radius if self.dragging else 6,
        )

        # Knob inner dot
        if self.dragging or self.hovered:
            pygame.draw.circle(
                surface, BG_DARK,
                (self.knob_x, self.track_rect.centery), 3,
            )


class StatsPanel:
    """Displays real-time sorting statistics."""

    def __init__(self, x, y, w):
        self.x = x
        self.y = y
        self.w = w
        self.comparisons = 0
        self.accesses = 0
        self.elapsed_ms = 0.0
        self.algorithm_name = ""

    def draw(self, surface):
        font_label = Font.get(11)
        font_value = Font.get(14, bold=True)

        y = self.y

        # Algorithm name
        if self.algorithm_name:
            name_surf = Font.get(16, bold=True).render(
                self.algorithm_name, True, ACCENT_CYAN
            )
            surface.blit(name_surf, (self.x, y))
            y += 28

        # Divider
        pygame.draw.line(surface, DIVIDER, (self.x, y), (self.x + self.w, y))
        y += 10

        stats = [
            ("Comparisons", f"{self.comparisons:,}", ACCENT_GREEN),
            ("Array Accesses", f"{self.accesses:,}", ACCENT_ORANGE),
            ("Elapsed", f"{self.elapsed_ms:.0f} ms", TEXT_PRIMARY),
        ]

        for label, value, color in stats:
            label_surf = font_label.render(label, True, TEXT_DIM)
            value_surf = font_value.render(value, True, color)
            surface.blit(label_surf, (self.x, y))
            y += 16
            surface.blit(value_surf, (self.x, y))
            y += 24
