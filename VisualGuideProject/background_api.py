import time

from config import (
    BACKGROUND_CAPTURE_FRAME_DELAY_SECONDS,
    BACKGROUND_CAPTURE_FRAMES,
    BACKGROUND_SETTLE_SECONDS,
)


class BackgroundCaptureCancelled(Exception):
    pass


def capture_stable_background(
    camera,
    vision,
    settle_seconds=BACKGROUND_SETTLE_SECONDS,
    frame_count=BACKGROUND_CAPTURE_FRAMES,
    frame_delay_seconds=BACKGROUND_CAPTURE_FRAME_DELAY_SECONDS,
    progress_callback=None,
):
    """
    Capture a stable empty background from several frames.

    The progress callback can return False to cancel capture.
    """
    last_frame = None

    settle_start = time.monotonic()
    while time.monotonic() - settle_start < settle_seconds:
        last_frame = camera.get_frame()
        remaining = max(0.0, settle_seconds - (time.monotonic() - settle_start))

        if progress_callback is not None:
            keep_going = progress_callback(
                frame=last_frame,
                phase="settling",
                remaining_seconds=remaining,
                frame_index=0,
                frame_count=frame_count,
            )

            if keep_going is False:
                raise BackgroundCaptureCancelled()

        time.sleep(frame_delay_seconds)

    frames = []

    for index in range(frame_count):
        last_frame = camera.get_frame()
        frames.append(last_frame)

        if progress_callback is not None:
            keep_going = progress_callback(
                frame=last_frame,
                phase="capturing",
                remaining_seconds=0.0,
                frame_index=index + 1,
                frame_count=frame_count,
            )

            if keep_going is False:
                raise BackgroundCaptureCancelled()

        time.sleep(frame_delay_seconds)

    vision.capture_background_from_frames(frames)
    return frames[-1] if frames else last_frame
