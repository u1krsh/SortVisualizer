"""
main.py — Entry point for the Sorting Algorithm Visualizer.

The Sound of Sorting — Python Edition
Visualizes sorting algorithms with real-time sound generation.
"""

import sys
import pygame
from visualizer import SortVisualizer


def main():
    """Initialize pygame and run the main application loop."""
    pygame.init()
    pygame.display.set_caption("The Sound of Sorting — Visualizer")

    # Window setup
    WIDTH, HEIGHT = 1100, 650
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    FPS = 60

    # Create visualizer
    viz = SortVisualizer(WIDTH, HEIGHT)
    viz.setup_ui()

    # Main loop
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if viz.sorting:
                        viz.stop_sorting()
                    else:
                        viz.start_sorting()
                elif event.key == pygame.K_r:
                    if not viz.sorting:
                        viz._shuffle_array()
                        viz._reset_stats()

        viz.update(events)
        viz.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    # Cleanup
    viz.sound.cleanup()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
