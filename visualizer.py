"""
visualizer.py — Core sorting visualizer with rendering and orchestration.

Manages the array state, draws the bar visualization, runs sorting generators,
and coordinates sound + UI updates.
"""

import random
import time

import pygame

from algorithms import ALGORITHMS, ALGORITHM_NAMES
from sound import SoundEngine
from ui import (
    BG_DARK, BG_PANEL, BG_PANEL_BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    ACCENT_CYAN, ACCENT_MAGENTA, ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE,
    DIVIDER, Font, Button, Slider, StatsPanel, draw_rounded_rect, lerp_color,
)


# ─── Bar Colors ──────────────────────────────────────────────────────────────
BAR_COLOR = (50, 120, 220)             # Plain blue for all bars
BAR_HIGHLIGHT = (255, 60, 60)          # Red for active comparison/access
BAR_SWAP = (255, 200, 40)              # Yellow-orange for swaps
BAR_SORTED = (0, 255, 140)             # Green for sorted confirmation
BAR_SET = (255, 120, 0)                # Orange for set operations


class SortVisualizer:
    """Main visualizer that orchestrates sorting, rendering, and sound."""

    PANEL_WIDTH = 240
    TOP_BAR_HEIGHT = 0
    BOTTOM_BAR_HEIGHT = 40

    def __init__(self, screen_width=1100, screen_height=650):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.viz_width = screen_width - self.PANEL_WIDTH
        self.viz_height = screen_height - self.TOP_BAR_HEIGHT - self.BOTTOM_BAR_HEIGHT

        # Array state
        self.array_size = 100
        self.array: list[int] = []
        self.max_value = self.array_size

        # Sorting state
        self.sorting = False
        self.paused = False
        self.sort_generator = None
        self.current_algorithm = "Bubble Sort"
        self.highlighted: dict[int, tuple] = {}  # index -> color
        self.sorted_indices: set[int] = set()
        self.completion_sweep = None
        self.sweep_index = 0

        # Stats
        self.comparisons = 0
        self.accesses = 0
        self.start_time = 0.0
        self.elapsed_ms = 0.0

        # Speed control: operations per frame
        self.speed = 5
        self.max_speed = 200

        # Sound
        self.sound = SoundEngine()

        # Initialize array
        self._shuffle_array()

        # UI elements will be created by setup_ui()
        self.algo_buttons: list[Button] = []
        self.btn_shuffle: Button | None = None
        self.btn_start: Button | None = None
        self.btn_stop: Button | None = None
        self.btn_sound: Button | None = None
        self.slider_size: Slider | None = None
        self.slider_speed: Slider | None = None
        self.slider_volume: Slider | None = None
        self.stats_panel: StatsPanel | None = None

    def setup_ui(self):
        """Create all UI elements. Call after pygame.init()."""
        panel_x = self.viz_width + 16
        panel_w = self.PANEL_WIDTH - 32
        y = 16

        # Title
        self._title_y = y
        y += 40

        # Algorithm buttons
        self.algo_buttons = []
        for i, name in enumerate(ALGORITHM_NAMES):
            btn = Button(
                panel_x, y + i * 36, panel_w, 30, name,
                font_size=13, toggle=True,
            )
            if name == self.current_algorithm:
                btn.active = True
            self.algo_buttons.append(btn)
        y += len(ALGORITHM_NAMES) * 36 + 12

        # Size slider
        self.slider_size = Slider(
            panel_x, y, panel_w, "Array Size",
            16, 512, self.array_size, step=1,
            value_format=lambda v: str(int(v)),
        )
        y += 48

        # Speed slider
        self.slider_speed = Slider(
            panel_x, y, panel_w, "Speed",
            1, self.max_speed, self.speed, step=1,
            value_format=lambda v: f"{int(v)} ops/frame",
        )
        y += 48

        # Volume slider
        self.slider_volume = Slider(
            panel_x, y, panel_w, "Volume",
            0, 100, int(self.sound.volume * 100), step=1,
            value_format=lambda v: f"{int(v)}%",
        )
        y += 52

        # Control buttons
        btn_w = (panel_w - 8) // 2
        self.btn_shuffle = Button(panel_x, y, btn_w, 32, "Shuffle", font_size=13)
        self.btn_start = Button(panel_x + btn_w + 8, y, btn_w, 32, "Start",
                                font_size=13, accent=(0, 140, 100))
        y += 40
        self.btn_stop = Button(panel_x, y, btn_w, 32, "Stop", font_size=13,
                               accent=(140, 40, 40))
        self.btn_sound = Button(panel_x + btn_w + 8, y, btn_w, 32, "Sound",
                                font_size=13, toggle=True)
        self.btn_sound.active = True
        y += 48

        # Stats panel
        self.stats_panel = StatsPanel(panel_x, y, panel_w)
        self.stats_panel.algorithm_name = self.current_algorithm

    def _shuffle_array(self):
        """Create a new shuffled array of values 1..n."""
        self.array = list(range(1, self.array_size + 1))
        random.shuffle(self.array)
        self.max_value = self.array_size
        self.highlighted.clear()
        self.sorted_indices.clear()
        self.completion_sweep = None
        self.sweep_index = 0

    def _reset_stats(self):
        """Reset all counters."""
        self.comparisons = 0
        self.accesses = 0
        self.start_time = time.perf_counter()
        self.elapsed_ms = 0.0

    def start_sorting(self):
        """Begin sorting with the selected algorithm."""
        if self.sorting:
            return
        self._shuffle_array()
        self._reset_stats()
        algo_func = ALGORITHMS[self.current_algorithm]
        self.sort_generator = algo_func(self.array)
        self.sorting = True
        self.paused = False
        self.completion_sweep = None

    def stop_sorting(self):
        """Stop the current sort."""
        self.sorting = False
        self.paused = False
        self.sort_generator = None
        self.highlighted.clear()
        self.completion_sweep = None

    def _process_operation(self, op):
        """Process a single sorting operation tuple."""
        self.highlighted.clear()

        op_type = op[0]

        if op_type == "compare":
            i, j = op[1], op[2]
            self.comparisons += 1
            self.accesses += 2
            self.highlighted[i] = BAR_HIGHLIGHT
            self.highlighted[j] = BAR_HIGHLIGHT
            # Play tones for both compared values
            self.sound.play_tone(self.array[i], self.max_value)
            self.sound.play_tone(self.array[j], self.max_value)

        elif op_type == "swap":
            i, j = op[1], op[2]
            self.accesses += 4  # 2 reads + 2 writes
            self.highlighted[i] = BAR_SWAP
            self.highlighted[j] = BAR_SWAP
            self.sound.play_tone(self.array[i], self.max_value)
            self.sound.play_tone(self.array[j], self.max_value)

        elif op_type == "set":
            i = op[1]
            self.accesses += 1
            self.highlighted[i] = BAR_SET
            self.sound.play_tone(self.array[i], self.max_value)

        elif op_type == "access":
            i = op[1]
            self.accesses += 1
            self.highlighted[i] = BAR_HIGHLIGHT
            self.sound.play_tone(self.array[i], self.max_value)

        elif op_type == "done":
            self.sorting = False
            self.sort_generator = None
            self.highlighted.clear()
            # Start completion sweep
            self.completion_sweep = True
            self.sweep_index = 0

    def update(self, events):
        """Update one frame of the visualizer."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # Update UI elements
        for i, btn in enumerate(self.algo_buttons):
            btn.enabled = not self.sorting
            if btn.update(mouse_pos, mouse_pressed, events):
                # Deselect all others
                for j, other in enumerate(self.algo_buttons):
                    other.active = (j == i)
                self.current_algorithm = ALGORITHM_NAMES[i]
                if self.stats_panel:
                    self.stats_panel.algorithm_name = self.current_algorithm

        if self.slider_size:
            self.slider_size.enabled = not self.sorting
            if self.slider_size.update(mouse_pos, mouse_pressed, events):
                new_size = int(self.slider_size.value)
                if new_size != self.array_size:
                    self.array_size = new_size
                    self._shuffle_array()

        if self.slider_speed:
            if self.slider_speed.update(mouse_pos, mouse_pressed, events):
                self.speed = int(self.slider_speed.value)

        if self.slider_volume:
            if self.slider_volume.update(mouse_pos, mouse_pressed, events):
                self.sound.volume = self.slider_volume.value / 100.0

        if self.btn_shuffle and self.btn_shuffle.update(mouse_pos, mouse_pressed, events):
            if not self.sorting:
                self._shuffle_array()
                self._reset_stats()

        if self.btn_start and self.btn_start.update(mouse_pos, mouse_pressed, events):
            if not self.sorting:
                self.start_sorting()

        if self.btn_stop and self.btn_stop.update(mouse_pos, mouse_pressed, events):
            self.stop_sorting()

        if self.btn_sound and self.btn_sound.update(mouse_pos, mouse_pressed, events):
            self.sound.enabled = self.btn_sound.active

        # Update button states
        if self.btn_start:
            self.btn_start.enabled = not self.sorting
        if self.btn_stop:
            self.btn_stop.enabled = self.sorting
        if self.btn_shuffle:
            self.btn_shuffle.enabled = not self.sorting

        # Process sorting operations
        if self.sorting and self.sort_generator and not self.paused:
            ops_this_frame = self.speed
            for _ in range(ops_this_frame):
                if not self.sort_generator:
                    break
                try:
                    op = next(self.sort_generator)
                    self._process_operation(op)
                except StopIteration:
                    self.sorting = False
                    self.sort_generator = None
                    self.highlighted.clear()
                    self.completion_sweep = True
                    self.sweep_index = 0
                    break

            # Update elapsed time
            self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000

        # Process completion sweep
        if self.completion_sweep:
            sweep_speed = max(2, self.array_size // 30)
            for _ in range(sweep_speed):
                if self.sweep_index < len(self.array):
                    self.sorted_indices.add(self.sweep_index)
                    self.sound.play_tone(
                        self.array[self.sweep_index], self.max_value
                    )
                    self.sweep_index += 1
                else:
                    self.completion_sweep = None
                    break

        # Update stats panel
        if self.stats_panel:
            self.stats_panel.comparisons = self.comparisons
            self.stats_panel.accesses = self.accesses
            self.stats_panel.elapsed_ms = self.elapsed_ms

    def draw(self, surface: pygame.Surface):
        """Render the full visualizer."""
        surface.fill(BG_DARK)

        self._draw_bars(surface)
        self._draw_panel(surface)
        self._draw_bottom_bar(surface)

    def _draw_bars(self, surface: pygame.Surface):
        """Draw the array as vertical bars."""
        n = len(self.array)
        if n == 0:
            return

        area_x = 8
        area_y = self.TOP_BAR_HEIGHT + 8
        area_w = self.viz_width - 16
        area_h = self.viz_height - 16

        bar_total_width = area_w / n
        bar_width = max(1, int(bar_total_width * 0.85))
        gap = bar_total_width - bar_width

        for i, value in enumerate(self.array):
            # Bar height proportional to value
            bar_height = max(1, int((value / self.max_value) * area_h))
            x = area_x + int(i * bar_total_width)
            y = area_y + area_h - bar_height

            # Determine color
            if i in self.highlighted:
                color = self.highlighted[i]
            elif i in self.sorted_indices:
                color = BAR_SORTED
            else:
                color = BAR_COLOR

            # Draw bar
            bar_rect = pygame.Rect(x, y, max(1, bar_width), bar_height)
            pygame.draw.rect(surface, color, bar_rect)

    def _draw_panel(self, surface: pygame.Surface):
        """Draw the right-side control panel."""
        panel_rect = pygame.Rect(
            self.viz_width, 0, self.PANEL_WIDTH, self.screen_height
        )
        draw_rounded_rect(surface, BG_PANEL, panel_rect, radius=0)

        # Panel border
        pygame.draw.line(
            surface, BG_PANEL_BORDER,
            (self.viz_width, 0), (self.viz_width, self.screen_height), 1
        )

        # Title
        title_font = Font.get(18, bold=True)
        title_surf = title_font.render("Sort Visualizer", True, TEXT_PRIMARY)
        surface.blit(title_surf, (self.viz_width + 16, self._title_y))

        # Subtitle
        sub_font = Font.get(10)
        sub_surf = sub_font.render("Sound of Sorting", True, TEXT_DIM)
        surface.blit(sub_surf, (self.viz_width + 16, self._title_y + 22))

        # Draw all UI elements
        for btn in self.algo_buttons:
            btn.draw(surface)

        if self.slider_size:
            self.slider_size.draw(surface)
        if self.slider_speed:
            self.slider_speed.draw(surface)
        if self.slider_volume:
            self.slider_volume.draw(surface)

        if self.btn_shuffle:
            self.btn_shuffle.draw(surface)
        if self.btn_start:
            self.btn_start.draw(surface)
        if self.btn_stop:
            self.btn_stop.draw(surface)
        if self.btn_sound:
            self.btn_sound.draw(surface)

        if self.stats_panel:
            self.stats_panel.draw(surface)

    def _draw_bottom_bar(self, surface: pygame.Surface):
        """Draw the bottom status bar."""
        bar_y = self.screen_height - self.BOTTOM_BAR_HEIGHT
        bar_rect = pygame.Rect(0, bar_y, self.viz_width, self.BOTTOM_BAR_HEIGHT)
        pygame.draw.rect(surface, (15, 15, 35), bar_rect)
        pygame.draw.line(
            surface, DIVIDER, (0, bar_y), (self.viz_width, bar_y)
        )

        font = Font.get(11)
        # Left: array info
        info_text = f"Array: [1..{self.array_size}]  |  {self.array_size} elements"
        info_surf = font.render(info_text, True, TEXT_DIM)
        surface.blit(info_surf, (12, bar_y + 12))

        # Right: status
        if self.sorting:
            status = "● SORTING"
            status_color = ACCENT_GREEN
        elif self.completion_sweep:
            status = "✓ COMPLETE"
            status_color = ACCENT_GREEN
        else:
            status = "○ IDLE"
            status_color = TEXT_DIM

        status_surf = font.render(status, True, status_color)
        surface.blit(
            status_surf,
            (self.viz_width - status_surf.get_width() - 12, bar_y + 12),
        )
