import math
import time

from config import (
    BACKGROUND_DETECTION_STABLE_FRAMES,
    BOX_MATCH_CENTER_DISTANCE_RATIO,
    BOX_MATCH_IOU_THRESHOLD,
    BOX_SMOOTHING_ALPHA,
    CLEAR_STABLE_FRAMES,
    DETECTION_HOLD_FRAMES,
    STABILITY_ENABLED,
    URGENT_WARNING_STABLE_FRAMES,
    WARNING_CHANGE_MIN_SECONDS,
    WARNING_STABLE_FRAMES,
)


def _has_detection(detection):
    return detection is not None and detection.get("bbox") is not None


def _is_urgent_warning(warning):
    if not warning:
        return False

    warning_lower = warning.lower()
    return "stop" in warning_lower and "ahead" in warning_lower


def _box_iou(box_a, box_b):
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b

    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh

    intersection_x1 = max(ax, bx)
    intersection_y1 = max(ay, by)
    intersection_x2 = min(ax2, bx2)
    intersection_y2 = min(ay2, by2)

    intersection_width = max(0, intersection_x2 - intersection_x1)
    intersection_height = max(0, intersection_y2 - intersection_y1)
    intersection_area = intersection_width * intersection_height

    if intersection_area == 0:
        return 0.0

    area_a = aw * ah
    area_b = bw * bh
    union_area = area_a + area_b - intersection_area

    if union_area <= 0:
        return 0.0

    return intersection_area / union_area


def _center_distance(center_a, center_b):
    ax, ay = center_a
    bx, by = center_b
    return math.hypot(ax - bx, ay - by)


class DetectionStabilizer:
    def __init__(self):
        self.smoothed_detection = None
        self.missing_detection_frames = 0
        self.stable_warning = None
        self.pending_warning = None
        self.pending_warning_frames = 0
        self.clear_warning_frames = 0
        self.last_warning_change_time = 0.0

    def reset(self):
        self.smoothed_detection = None
        self.missing_detection_frames = 0
        self.stable_warning = None
        self.pending_warning = None
        self.pending_warning_frames = 0
        self.clear_warning_frames = 0
        self.last_warning_change_time = 0.0

    def stabilize_detection(self, detection, frame_width, frame_height):
        if not STABILITY_ENABLED:
            return detection

        if not _has_detection(detection):
            self.missing_detection_frames += 1

            if (
                self.smoothed_detection is not None
                and self.missing_detection_frames <= DETECTION_HOLD_FRAMES
            ):
                held_detection = self.smoothed_detection.copy()
                held_detection["held"] = True
                return held_detection

            self.smoothed_detection = None
            return None

        self.missing_detection_frames = 0
        detection_copy = detection.copy()

        if self.smoothed_detection is None:
            self.smoothed_detection = detection_copy
            return detection_copy

        if not self._matches_previous_target(detection_copy, frame_width, frame_height):
            self.smoothed_detection = detection_copy
            return detection_copy

        self.smoothed_detection = self._smooth_detection(
            self.smoothed_detection,
            detection_copy,
            frame_width,
            frame_height,
        )
        return self.smoothed_detection.copy()

    def stabilize_warning(self, warning):
        if not STABILITY_ENABLED:
            return warning

        current_time = time.monotonic()

        if warning is None:
            self.pending_warning = None
            self.pending_warning_frames = 0
            self.clear_warning_frames += 1

            if self.clear_warning_frames >= CLEAR_STABLE_FRAMES:
                self.stable_warning = None

            return self.stable_warning

        self.clear_warning_frames = 0

        if warning == self.stable_warning:
            self.pending_warning = None
            self.pending_warning_frames = 0
            return self.stable_warning

        if warning == self.pending_warning:
            self.pending_warning_frames += 1
        else:
            self.pending_warning = warning
            self.pending_warning_frames = 1

        required_frames = WARNING_STABLE_FRAMES

        if _is_urgent_warning(warning):
            required_frames = URGENT_WARNING_STABLE_FRAMES

        enough_frames = self.pending_warning_frames >= required_frames
        enough_time = (
            current_time - self.last_warning_change_time >= WARNING_CHANGE_MIN_SECONDS
        )

        if enough_frames and (enough_time or _is_urgent_warning(warning)):
            self.stable_warning = warning
            self.last_warning_change_time = current_time
            self.pending_warning = None
            self.pending_warning_frames = 0

        return self.stable_warning

    def _matches_previous_target(self, detection, frame_width, frame_height):
        previous_bbox = self.smoothed_detection.get("bbox")
        current_bbox = detection.get("bbox")

        if previous_bbox is None or current_bbox is None:
            return False

        if _box_iou(previous_bbox, current_bbox) >= BOX_MATCH_IOU_THRESHOLD:
            return True

        previous_center = self.smoothed_detection.get("center")
        current_center = detection.get("center")

        if previous_center is None or current_center is None:
            return False

        frame_diagonal = math.hypot(frame_width, frame_height)
        max_distance = frame_diagonal * BOX_MATCH_CENTER_DISTANCE_RATIO

        return _center_distance(previous_center, current_center) <= max_distance

    def _smooth_detection(self, previous, current, frame_width, frame_height):
        alpha = BOX_SMOOTHING_ALPHA
        previous_bbox = previous["bbox"]
        current_bbox = current["bbox"]

        smoothed_bbox = tuple(
            int(round((1 - alpha) * previous_value + alpha * current_value))
            for previous_value, current_value in zip(previous_bbox, current_bbox)
        )

        x, y, w, h = smoothed_bbox
        w = max(1, w)
        h = max(1, h)
        cx = x + w // 2
        cy = y + h // 2
        box_area = w * h
        frame_area = frame_width * frame_height

        smoothed = current.copy()
        smoothed["bbox"] = (x, y, w, h)
        smoothed["center"] = (cx, cy)
        smoothed["box_area"] = box_area
        smoothed["area_ratio"] = box_area / frame_area if frame_area else 0
        smoothed["smoothed"] = True

        return smoothed


class DetectionPersistenceFilter:
    def __init__(self, required_frames=BACKGROUND_DETECTION_STABLE_FRAMES):
        self.required_frames = max(1, required_frames)
        self.previous_detection = None
        self.match_count = 0

    def reset(self):
        self.previous_detection = None
        self.match_count = 0

    def update(self, detection, frame_width, frame_height):
        if not _has_detection(detection):
            self.reset()
            return None

        if self.previous_detection is None:
            self.previous_detection = detection.copy()
            self.match_count = 1
        elif self._matches_previous(detection, frame_width, frame_height):
            self.previous_detection = detection.copy()
            self.match_count += 1
        else:
            self.previous_detection = detection.copy()
            self.match_count = 1

        if self.match_count >= self.required_frames:
            stable_detection = detection.copy()
            stable_detection["persistent"] = True
            return stable_detection

        return None

    def _matches_previous(self, detection, frame_width, frame_height):
        previous_bbox = self.previous_detection.get("bbox")
        current_bbox = detection.get("bbox")

        if previous_bbox is None or current_bbox is None:
            return False

        if _box_iou(previous_bbox, current_bbox) >= BOX_MATCH_IOU_THRESHOLD:
            return True

        previous_center = self.previous_detection.get("center")
        current_center = detection.get("center")

        if previous_center is None or current_center is None:
            return False

        frame_diagonal = math.hypot(frame_width, frame_height)
        max_distance = frame_diagonal * BOX_MATCH_CENTER_DISTANCE_RATIO

        return _center_distance(previous_center, current_center) <= max_distance
