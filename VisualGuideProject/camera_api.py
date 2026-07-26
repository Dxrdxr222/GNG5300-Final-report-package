# camera_api.py

import cv2
import platform
import time

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    CAMERA_FPS,
    DROP_OLD_FRAMES,
)


class CameraAPI:
    def __init__(self, camera_index=CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None

    def start(self):
        system_name = platform.system().lower()

        # On Linux / Raspberry Pi, V4L2 usually gives lower latency.
        if "linux" in system_name:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        elif "windows" in system_name:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened() and "windows" in system_name:
            self.cap.release()
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(f"Camera could not be opened. Index: {self.camera_index}")

        # Reduce buffering if backend supports it.
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Set camera resolution.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        # Set FPS if backend supports it.
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        print("Camera started successfully.")
        print(f"Requested size: {FRAME_WIDTH} x {FRAME_HEIGHT}")
        print(f"Actual size: {actual_width} x {actual_height}")
        print(f"Actual FPS: {actual_fps}")

    def get_frame(self):
        if self.cap is None:
            raise RuntimeError("Camera has not been started.")

        # Drop old buffered frames so we process a fresher image.
        for _ in range(DROP_OLD_FRAMES):
            self.cap.grab()

        ret, frame = self.cap.read()

        retry_count = 0
        while (not ret or frame is None) and retry_count < 3:
            time.sleep(0.05)
            ret, frame = self.cap.read()
            retry_count += 1

        if not ret or frame is None:
            raise RuntimeError("Failed to read frame from camera.")

        height, width = frame.shape[:2]

        if width != FRAME_WIDTH or height != FRAME_HEIGHT:
            frame = cv2.resize(
                frame,
                (FRAME_WIDTH, FRAME_HEIGHT),
                interpolation=cv2.INTER_AREA,
            )

        return frame

    def stop(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("Camera stopped.")


def camera_is_available(camera_index=CAMERA_INDEX):
    """
    Quickly check whether a camera can be opened.

    Used by Raspberry Pi standby mode so the program can wait quietly until the
    user plugs in the camera.
    """
    system_name = platform.system().lower()

    if "linux" in system_name:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    elif "windows" in system_name:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened() and "windows" in system_name:
        cap.release()
        cap = cv2.VideoCapture(camera_index)

    available = cap.isOpened()
    cap.release()

    return available
