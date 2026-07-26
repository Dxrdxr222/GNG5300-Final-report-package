# pi_visual_guide.py

import time

from camera_api import camera_is_available
from config import (
    CAMERA_INDEX,
    CAMERA_STANDBY_PRINT_SECONDS,
    CAMERA_WAIT_RETRY_SECONDS,
)
from visual_guide_runtime import (
    SESSION_CAMERA_LOST,
    SESSION_USER_QUIT,
    run_visual_guide_session,
)


def run_pi_visual_guide(camera_index=CAMERA_INDEX):
    """
    Raspberry Pi production launcher.

    Behavior:

    - terminal opens and stays alive
    - no camera plugged in: standby loop
    - camera plugged in: start visual guide session
    - camera unplugged: stop session and return to standby
    - q / Ctrl+C: quit program
    """
    print("Visual Guide Robot - Raspberry Pi Mode")
    print("Standby gate: plug in the camera to start.")
    print("Unplug the camera to return to standby.")
    print("Press q in the camera window or Ctrl+C in terminal to quit.")
    print("")

    last_standby_print = 0.0

    while True:
        now = time.monotonic()

        if not camera_is_available(camera_index):
            if now - last_standby_print >= CAMERA_STANDBY_PRINT_SECONDS:
                print(
                    "STANDBY: waiting for camera "
                    f"index {camera_index}. Plug in camera to start."
                )
                last_standby_print = now

            time.sleep(CAMERA_WAIT_RETRY_SECONDS)
            continue

        print(f"CAMERA GATE: camera index {camera_index} detected.")
        print("Starting continuous visual guide session...")

        status = run_visual_guide_session(
            camera_index=camera_index,
            window_name="Visual Guide Robot - Pi",
        )

        if status == SESSION_USER_QUIT:
            print("User quit requested. Visual Guide Robot stopped.")
            break

        if status == SESSION_CAMERA_LOST:
            print("CAMERA GATE: camera lost/unplugged. Returning to standby.")
        else:
            print(f"Visual guide session ended with status: {status}.")
            print("Returning to standby.")

        last_standby_print = 0.0
        time.sleep(CAMERA_WAIT_RETRY_SECONDS)


def main():
    try:
        run_pi_visual_guide()
    except KeyboardInterrupt:
        print("")
        print("Ctrl+C received. Visual Guide Robot stopped.")


if __name__ == "__main__":
    main()
