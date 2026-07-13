"""
sound.py — Triangle wave synthesis with ADSR envelope for sorting visualizer.

Generates short tones mapped to array values (120 Hz – 1212 Hz),
played via pygame.mixer for the "8-bit game tune" effect.
"""

import numpy as np
import pygame


class SoundEngine:
    """Manages audio synthesis and playback for the sorting visualizer."""

    SAMPLE_RATE = 44100
    FREQ_MIN = 120.0
    FREQ_MAX = 1212.0
    CHANNELS = 8

    def __init__(self):
        pygame.mixer.pre_init(
            frequency=self.SAMPLE_RATE,
            size=-16,
            channels=1,
            buffer=512,
        )
        pygame.mixer.init()
        pygame.mixer.set_num_channels(self.CHANNELS)

        self._tone_cache: dict[int, pygame.mixer.Sound] = {}
        self._enabled = True
        self._duration = 0.05  # seconds per tone
        self._volume = 0.5  # 0.0 to 1.0
        self._channel_index = 0

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        if not value:
            pygame.mixer.stop()

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(1.0, value))
        self._tone_cache.clear()

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, value: float):
        self._duration = max(0.01, min(0.15, value))
        self._tone_cache.clear()

    def _make_tone(self, frequency: float) -> pygame.mixer.Sound:
        """Generate a triangle wave tone with ADSR envelope."""
        n_samples = int(self.SAMPLE_RATE * self._duration)
        t = np.linspace(0, self._duration, n_samples, dtype=np.float64)

        # Triangle wave synthesis
        period = 1.0 / frequency
        phase = (t % period) / period
        wave = 2.0 * np.abs(2.0 * phase - 1.0) - 1.0

        # ADSR envelope
        attack = 0.005   # 5ms
        decay = 0.01     # 10ms
        sustain_level = 0.6
        release = min(0.015, self._duration * 0.3)  # 15ms or 30% of duration

        envelope = np.ones(n_samples, dtype=np.float64)

        # Attack phase
        attack_samples = int(attack * self.SAMPLE_RATE)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Decay phase
        decay_start = attack_samples
        decay_samples = int(decay * self.SAMPLE_RATE)
        if decay_samples > 0 and decay_start + decay_samples < n_samples:
            envelope[decay_start:decay_start + decay_samples] = np.linspace(
                1.0, sustain_level, decay_samples
            )
            envelope[decay_start + decay_samples:] = sustain_level

        # Release phase
        release_samples = int(release * self.SAMPLE_RATE)
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(
                sustain_level, 0, release_samples
            )

        # Apply envelope and normalize
        wave *= envelope
        wave *= 0.3 * self._volume  # Master volume scaled by user volume
        samples = (wave * 32767).astype(np.int16)

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _freq_for_value(self, value: int, max_value: int) -> float:
        """Map an array value to a frequency in the 120–1212 Hz range."""
        if max_value <= 1:
            return self.FREQ_MIN
        ratio = (value - 1) / (max_value - 1)
        return self.FREQ_MIN + ratio * (self.FREQ_MAX - self.FREQ_MIN)

    def play_tone(self, value: int, max_value: int):
        """Play a short tone corresponding to the given array value."""
        if not self._enabled:
            return

        freq = self._freq_for_value(value, max_value)
        freq_key = int(freq)

        if freq_key not in self._tone_cache:
            self._tone_cache[freq_key] = self._make_tone(freq)

        sound = self._tone_cache[freq_key]

        # Round-robin channels for polyphonic mixing
        channel = pygame.mixer.Channel(self._channel_index % self.CHANNELS)
        channel.play(sound)
        self._channel_index = (self._channel_index + 1) % self.CHANNELS

    def play_completion_sweep(self, array: list[int], max_value: int):
        """Return a generator that plays a sweep tone for completion."""
        for val in array:
            self.play_tone(val, max_value)
            yield

    def cleanup(self):
        """Stop all sounds and clean up."""
        pygame.mixer.stop()
        self._tone_cache.clear()
