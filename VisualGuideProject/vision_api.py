# vision_api.py

import cv2
import numpy as np

from config import (
    BACKGROUND_CAPTURE_METHOD,
    MIN_CONTOUR_AREA,
    THRESHOLD_VALUE,
    MAX_DETECTION_AREA_RATIO,
    BLUR_KERNEL_SIZE,
    DILATION_ITERATIONS,
    MAX_OBJECTS,
    MOTION_OBJECT_BLUR_KERNEL_SIZE,
    MOTION_OBJECT_DILATION_ITERATIONS,
    MOTION_OBJECT_MAX_AREA_RATIO,
    MOTION_OBJECT_MIN_AREA,
    MOTION_OBJECT_THRESHOLD_VALUE,
)


class VisionAPI:
    def __init__(self):
        self.background_gray = None
        self.previous_motion_gray = None

    def _prepare_gray(self, frame, blur_kernel_size):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)
        return gray

    def _extract_detections(self, mask, frame_area, source, min_area, max_area_ratio):
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        detections = []

        for contour in contours:
            contour_area = cv2.contourArea(contour)

            if contour_area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            box_area = w * h
            area_ratio = box_area / frame_area

            if area_ratio > max_area_ratio:
                continue

            moments = cv2.moments(contour)

            if moments["m00"] != 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
            else:
                cx = x + w // 2
                cy = y + h // 2

            detections.append(
                {
                    "bbox": (x, y, w, h),
                    "center": (cx, cy),
                    "box_area": box_area,
                    "area_ratio": area_ratio,
                    "source": source,
                    "mask": mask,
                }
            )

        detections = sorted(
            detections,
            key=lambda item: item["box_area"],
            reverse=True,
        )

        return detections[:MAX_OBJECTS]

    def capture_background(self, frame):
        """
        Capture the current empty background.
        Use this when the camera is stable and the view is mostly empty.
        """
        gray = self._prepare_gray(frame, BLUR_KERNEL_SIZE)

        self.background_gray = gray
        self.previous_motion_gray = None

        print("Background captured.")

    def capture_background_from_frames(self, frames):
        """
        Capture a robust background from multiple empty-view frames.
        """
        if not frames:
            raise ValueError("At least one frame is required to capture background.")

        if len(frames) == 1:
            self.capture_background(frames[0])
            return

        gray_frames = [
            self._prepare_gray(frame, BLUR_KERNEL_SIZE)
            for frame in frames
            if frame is not None
        ]

        if not gray_frames:
            raise ValueError("No valid frames were provided for background capture.")

        method = BACKGROUND_CAPTURE_METHOD.lower()

        if method == "mean":
            background = np.mean(gray_frames, axis=0).astype(np.uint8)
        else:
            background = np.median(gray_frames, axis=0).astype(np.uint8)

        self.background_gray = background
        self.previous_motion_gray = None

        print(
            f"Background captured from {len(gray_frames)} frames "
            f"using {method if method == 'mean' else 'median'}."
        )

    def detect_obstacles(self, frame):
        """
        Detect multiple changed objects compared with saved background.

        Return:
            detections: list of detection dictionaries
            mask: black/white threshold image
        """

        if self.background_gray is None:
            raise RuntimeError("Background has not been captured.")

        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_height * frame_width

        gray = self._prepare_gray(frame, BLUR_KERNEL_SIZE)

        frame_delta = cv2.absdiff(self.background_gray, gray)

        _, thresh = cv2.threshold(
            frame_delta,
            THRESHOLD_VALUE,
            255,
            cv2.THRESH_BINARY,
        )

        # Remove tiny noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # Connect nearby changed pixels
        thresh = cv2.dilate(thresh, None, iterations=DILATION_ITERATIONS)

        detections = self._extract_detections(
            mask=thresh,
            frame_area=frame_area,
            source="background",
            min_area=MIN_CONTOUR_AREA,
            max_area_ratio=MAX_DETECTION_AREA_RATIO,
        )

        return detections, thresh

    def detect_moving_objects(self, frame):
        """
        Detect objects that changed between consecutive frames.

        This is different from background detection: it ignores objects that are
        simply different from the saved background but no longer moving.
        """
        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_height * frame_width

        gray = self._prepare_gray(frame, MOTION_OBJECT_BLUR_KERNEL_SIZE)

        if self.previous_motion_gray is None:
            self.previous_motion_gray = gray
            return [], None

        frame_delta = cv2.absdiff(self.previous_motion_gray, gray)
        self.previous_motion_gray = gray

        _, thresh = cv2.threshold(
            frame_delta,
            MOTION_OBJECT_THRESHOLD_VALUE,
            255,
            cv2.THRESH_BINARY,
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.dilate(
            thresh,
            None,
            iterations=MOTION_OBJECT_DILATION_ITERATIONS,
        )

        detections = self._extract_detections(
            mask=thresh,
            frame_area=frame_area,
            source="motion",
            min_area=MOTION_OBJECT_MIN_AREA,
            max_area_ratio=MOTION_OBJECT_MAX_AREA_RATIO,
        )

        return detections, thresh
