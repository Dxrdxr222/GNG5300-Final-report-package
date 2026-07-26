# audio_alert_api.py

import math
import platform
import shutil
import struct
import subprocess
import threading
import time
import wave
from pathlib import Path

from config import (
    BEEP_PATTERN_APPROACH_AHEAD,
    BEEP_PATTERN_BICYCLE,
    BEEP_PATTERN_CAR,
    BEEP_PATTERN_DEFAULT,
    BEEP_PATTERN_STOP_AHEAD,
)


ALERT_PATTERNS = {
    "approach_ahead": BEEP_PATTERN_APPROACH_AHEAD,
    "stop_ahead": BEEP_PATTERN_STOP_AHEAD,
    "vehicle_car": BEEP_PATTERN_CAR,
    "vehicle_bicycle": BEEP_PATTERN_BICYCLE,
    "default": BEEP_PATTERN_DEFAULT,
}


class AudioAlertPlayer:
    """
    Play short, non-blocking beep patterns.

    Windows:
        Uses winsound.Beep.

    Linux / Raspberry Pi:
        Prefer aplay with tiny generated WAV files. If aplay is unavailable,
        fall back to terminal bell characters.

    The camera loop should never wait for a sound pattern to finish.
    """

    def __init__(self):
        self.thread = None
        self.lock = threading.Lock()
        self.cache_dir = Path(__file__).resolve().parent / "audio_cache"

    def is_playing(self):
        return self.thread is not None and self.thread.is_alive()

    def play(self, pattern_name):
        pattern = ALERT_PATTERNS.get(pattern_name, ALERT_PATTERNS["default"])

        with self.lock:
            if self.is_playing():
                return False

            self.thread = threading.Thread(
                target=self._play_pattern,
                args=(pattern_name, pattern),
                daemon=True,
            )
            self.thread.start()
            return True

    def _play_pattern(self, pattern_name, pattern):
        try:
            system_name = platform.system().lower()

            if "windows" in system_name:
                self._play_windows_pattern(pattern)
                return

            if "linux" in system_name and shutil.which("aplay"):
                wav_path = self._ensure_wave_file(pattern_name, pattern)
                subprocess.run(
                    ["aplay", "-q", str(wav_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                return

            self._play_terminal_pattern(pattern)

        except Exception as error:
            print(f"Audio alert failed: {error}")

    def _play_windows_pattern(self, pattern):
        import winsound

        for frequency_hz, duration_ms in pattern:
            if frequency_hz <= 0:
                time.sleep(duration_ms / 1000)
            else:
                winsound.Beep(int(frequency_hz), int(duration_ms))

    def _play_terminal_pattern(self, pattern):
        for frequency_hz, duration_ms in pattern:
            if frequency_hz > 0:
                print("\a", end="", flush=True)

            time.sleep(duration_ms / 1000)

    def _ensure_wave_file(self, pattern_name, pattern):
        self.cache_dir.mkdir(exist_ok=True)
        wav_path = self.cache_dir / f"{pattern_name}.wav"

        if wav_path.exists():
            return wav_path

        self._write_wave_file(wav_path, pattern)

        return wav_path

    def _write_wave_file(self, wav_path, pattern):
        sample_rate = 22050
        amplitude = int(32767 * 0.30)

        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            for frequency_hz, duration_ms in pattern:
                sample_count = int(sample_rate * duration_ms / 1000)

                for index in range(sample_count):
                    if frequency_hz <= 0:
                        sample = 0
                    else:
                        angle = 2 * math.pi * frequency_hz * index / sample_rate
                        sample = int(amplitude * math.sin(angle))

                    wav_file.writeframesraw(struct.pack("<h", sample))
