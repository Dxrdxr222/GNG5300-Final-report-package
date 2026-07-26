# output_api.py

import time
import platform
import subprocess

from audio_alert_api import AudioAlertPlayer
from config import (
    AUDIO_ENABLED,
    AUDIO_OUTPUT_MODE,
    BEEP_ON_APPROACHING_AHEAD,
    BEEP_ON_VEHICLE_WARNING,
    BEEP_ONLY_FOR_AHEAD,
    BEEP_REPEAT_SECONDS,
    BEEP_VEHICLE_LABELS,
    PRINT_ENABLED,
    SAME_WARNING_REPEAT_SECONDS,
    URGENT_WARNING_REPEAT_SECONDS,
    WARNING_RESET_SECONDS,
)

_last_message = None
_last_time = 0
_last_no_warning_time = 0
_speech_process = None
_last_beep_time = 0
_audio_alert_player = AudioAlertPlayer()
_audio_enabled_override = None


def set_audio_override(enabled):
    """
    Temporarily override AUDIO_ENABLED for controlled tests.

    Use None to return to config.py behavior.
    """
    global _audio_enabled_override

    _audio_enabled_override = enabled


def _audio_enabled():
    if _audio_enabled_override is None:
        return AUDIO_ENABLED

    return bool(_audio_enabled_override)


def print_warning(message):
    """
    Print warning only if PRINT_ENABLED = True in config.py.
    """
    if not PRINT_ENABLED:
        return

    if message:
        print(f"WARNING: {message}")


def _speech_is_running():
    """
    Check whether previous speech is still running.
    """
    global _speech_process

    if _speech_process is None:
        return False

    return _speech_process.poll() is None


def stop_speech():
    """
    Stop current speech if it is still running.
    """
    global _speech_process

    if _speech_process is not None and _speech_process.poll() is None:
        _speech_process.terminate()
        _speech_process = None


def _is_urgent(message):
    """
    Decide whether a warning is urgent.
    """
    if not message:
        return False

    message_lower = message.lower()

    return "stop" in message_lower or "ahead" in message_lower


def _message_words(message):
    normalized = message.lower()

    for character in ".,;:!?()[]{}":
        normalized = normalized.replace(character, " ")

    return set(normalized.split())


def _classify_beep_pattern(message):
    """
    Decide whether this stable warning deserves audio and which pattern to use.

    Current policy:
        1. approaching danger ahead
        2. YOLO-recognized vehicle warning: car or bicycle
    """
    if not message:
        return None

    message_lower = message.lower()
    words = _message_words(message)

    if BEEP_ON_VEHICLE_WARNING and "car" in words:
        return "vehicle_car"

    if BEEP_ON_VEHICLE_WARNING and "bicycle" in words:
        return "vehicle_bicycle"

    approaching_ahead = (
        BEEP_ON_APPROACHING_AHEAD
        and "approaching" in message_lower
        and "ahead" in message_lower
    )

    if approaching_ahead and "stop" in message_lower:
        return "stop_ahead"

    if approaching_ahead:
        return "approach_ahead"

    vehicle_warning = BEEP_ON_VEHICLE_WARNING and any(
        label.lower() in words for label in BEEP_VEHICLE_LABELS
    )

    if vehicle_warning:
        return "default"

    # Backward-compatible broad gate, kept for experiments.
    if BEEP_ONLY_FOR_AHEAD and _is_urgent(message):
        return "default"

    return None


def classify_beep_pattern(message):
    """
    Public helper for diagnostics.

    The live test uses this to report whether a warning message is supposed to
    create a beep. It does not play audio by itself.
    """
    return _classify_beep_pattern(message)


def _should_beep(message):
    return _classify_beep_pattern(message) is not None


def beep_warning(message, interrupt=False):
    """
    Play a short non-blocking beep for urgent ahead/stop warnings.
    """
    global _beep_thread, _last_beep_time

    if not _audio_enabled() or AUDIO_OUTPUT_MODE.lower() != "beep":
        return

    if not message:
        return

    pattern_name = _classify_beep_pattern(message)

    if pattern_name is None:
        return

    current_time = time.monotonic()

    if current_time - _last_beep_time < BEEP_REPEAT_SECONDS:
        return

    if _audio_alert_player.is_playing() and not interrupt:
        return

    _last_beep_time = current_time

    _audio_alert_player.play(pattern_name)


def speak_warning(message, interrupt=False):
    """
    Speak warning only if AUDIO_ENABLED = True in config.py.

    Windows:
        pyttsx3

    Linux / Raspberry Pi:
        espeak-ng, non-blocking
    """
    global _speech_process

    # Hard audio switch.
    # If AUDIO_ENABLED = False, this function cannot speak.
    if not _audio_enabled() or AUDIO_OUTPUT_MODE.lower() != "speech":
        return

    if not message:
        return

    system_name = platform.system().lower()

    if "windows" in system_name:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.say(message)
            engine.runAndWait()

        except Exception as error:
            print(f"Voice output failed: {error}")
            print_warning(message)

    elif "linux" in system_name:
        try:
            # Do not stack multiple voice outputs.
            if _speech_is_running():
                if interrupt:
                    stop_speech()
                else:
                    return

            # Non-blocking speech.
            # This does not freeze the camera loop.
            _speech_process = subprocess.Popen(["espeak-ng", message])

        except FileNotFoundError:
            print("espeak-ng is not installed.")
            print("Install it with: sudo apt install espeak-ng")
            print_warning(message)

    else:
        print_warning(message)


def reset_warning_state_if_clear():
    """
    If there is no warning for a short time, reset the last warning.

    This allows the same warning to be spoken again later if the obstacle
    disappears and then reappears.
    """
    global _last_message, _last_time, _last_no_warning_time

    current_time = time.monotonic()

    if _last_no_warning_time == 0:
        _last_no_warning_time = current_time
        return

    if current_time - _last_no_warning_time >= WARNING_RESET_SECONDS:
        _last_message = None
        _last_time = 0


def output_warning(message, mode=None, interrupt=False):
    """
    Output warning with anti-spam control.

    Important:
        This function is controlled by config.py:

        AUDIO_ENABLED = True / False
        AUDIO_OUTPUT_MODE = "beep" / "speech"
        PRINT_ENABLED = True / False

    The old 'mode' argument is ignored now.
    It is kept only so old calls like output_warning(message, mode="both")
    will not crash.
    """
    global _last_message, _last_time, _last_no_warning_time

    # If both output methods are disabled, do nothing.
    if not _audio_enabled() and not PRINT_ENABLED:
        return

    # No current warning
    if not message:
        reset_warning_state_if_clear()
        return

    # Since we have a warning now, reset no-warning timer.
    _last_no_warning_time = 0

    current_time = time.monotonic()

    if _is_urgent(message):
        repeat_seconds = URGENT_WARNING_REPEAT_SECONDS
    else:
        repeat_seconds = SAME_WARNING_REPEAT_SECONDS

    # If same message is still active, do not repeat too soon.
    if message == _last_message and current_time - _last_time < repeat_seconds:
        if AUDIO_OUTPUT_MODE.lower() == "beep":
            beep_warning(message, interrupt=interrupt)
        return

    # If speech is active and cannot be interrupted, skip only speech output.
    if (
        _audio_enabled()
        and AUDIO_OUTPUT_MODE.lower() == "speech"
        and _speech_is_running()
        and not interrupt
    ):
        return

    _last_message = message
    _last_time = current_time

    print_warning(message)

    if AUDIO_OUTPUT_MODE.lower() == "beep":
        beep_warning(message, interrupt=interrupt)
    else:
        speak_warning(message, interrupt=interrupt)
