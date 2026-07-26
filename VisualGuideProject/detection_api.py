# detection_api.py

import math

import config
from config import (
    BACKGROUND_PROCESS_INTERVAL,
    CLOSE_AREA_RATIO,
    MEDIUM_AREA_RATIO,
    MOTION_OBJECT_DETECTION_ENABLED,
    MOTION_OBJECT_PROCESS_INTERVAL,
)
from stability_api import DetectionPersistenceFilter


def has_detection(detection):
    return detection is not None and detection.get("bbox") is not None


def choose_primary_detection(detections, frame_width, frame_height, frame_area):
    """
    Choose the most important detection for warning.

    Priority:
        1. close center object
        2. close side object
        3. medium center object
        4. medium side object
        5. largest remaining object
    """

    if not detections:
        return None

    scored_detections = []

    left_boundary = frame_width / 3
    right_boundary = 2 * frame_width / 3
    top_boundary = frame_height / 3
    bottom_boundary = 2 * frame_height / 3

    for detection in detections:
        if not has_detection(detection):
            continue

        cx, cy = detection["center"]
        area_ratio = detection["box_area"] / frame_area

        if left_boundary <= cx <= right_boundary:
            direction_score = 2
        else:
            direction_score = 1

        if cy >= bottom_boundary:
            vertical_score = 2
        elif cy >= top_boundary:
            vertical_score = 1
        else:
            vertical_score = 0

        if area_ratio >= CLOSE_AREA_RATIO:
            closeness_score = 3
        elif area_ratio >= MEDIUM_AREA_RATIO:
            closeness_score = 2
        else:
            closeness_score = 1

        source_score = int(detection.get("priority_score", 0))
        if source_score == 0 and detection.get("source") == "motion":
            source_score = 20

        total_score = closeness_score * 100 + direction_score * 10 + vertical_score

        scored_detections.append(
            (total_score, source_score, detection["box_area"], detection)
        )

    if not scored_detections:
        return None

    scored_detections.sort(
        key=lambda item: (item[0], item[1], item[2]),
        reverse=True,
    )

    return scored_detections[0][3]


def _bbox_iou(first_bbox, second_bbox):
    first_x, first_y, first_w, first_h = first_bbox
    second_x, second_y, second_w, second_h = second_bbox

    first_right = first_x + first_w
    first_bottom = first_y + first_h
    second_right = second_x + second_w
    second_bottom = second_y + second_h

    overlap_left = max(first_x, second_x)
    overlap_top = max(first_y, second_y)
    overlap_right = min(first_right, second_right)
    overlap_bottom = min(first_bottom, second_bottom)

    overlap_width = max(0, overlap_right - overlap_left)
    overlap_height = max(0, overlap_bottom - overlap_top)
    overlap_area = overlap_width * overlap_height

    if overlap_area == 0:
        return 0.0

    first_area = first_w * first_h
    second_area = second_w * second_h
    union_area = first_area + second_area - overlap_area

    if union_area <= 0:
        return 0.0

    return overlap_area / union_area


def _center_distance_ratio(first_detection, second_detection, frame_width, frame_height):
    first_cx, first_cy = first_detection["center"]
    second_cx, second_cy = second_detection["center"]
    distance = math.hypot(first_cx - second_cx, first_cy - second_cy)
    frame_diagonal = math.hypot(frame_width, frame_height)

    if frame_diagonal == 0:
        return 1.0

    return distance / frame_diagonal


def _same_object_candidate(base_detection, yolo_detection, frame_width, frame_height):
    iou = _bbox_iou(base_detection["bbox"], yolo_detection["bbox"])

    if iou >= config.YOLO_LABEL_MATCH_IOU_THRESHOLD:
        return True

    center_ratio = _center_distance_ratio(
        base_detection,
        yolo_detection,
        frame_width,
        frame_height,
    )

    return center_ratio <= config.YOLO_LABEL_MATCH_CENTER_DISTANCE_RATIO


def attach_yolo_recognition(base_detection, yolo_detection, frame_width, frame_height):
    """
    Add YOLO object identity to a motion/background warning candidate.

    This keeps warning authority with the fast danger detectors, while letting
    YOLO answer "what object is this?" when the boxes likely refer to the same
    target.
    """

    if not has_detection(base_detection) or not has_detection(yolo_detection):
        return base_detection

    if base_detection.get("source") == "yolo":
        return base_detection

    if not _same_object_candidate(
        base_detection,
        yolo_detection,
        frame_width,
        frame_height,
    ):
        return base_detection

    enriched_detection = base_detection.copy()
    enriched_detection["label"] = yolo_detection.get("label")
    enriched_detection["confidence"] = yolo_detection.get("confidence")
    enriched_detection["danger_weight"] = yolo_detection.get("danger_weight")
    enriched_detection["recognized_by"] = "yolo"
    enriched_detection["recognition_bbox"] = yolo_detection.get("bbox")
    enriched_detection["recognition_center"] = yolo_detection.get("center")

    return enriched_detection


def combine_detections(
    frame_width,
    frame_height,
    frame_area,
    *detections,
    recognition_detection=None,
):
    """
    Select the most dangerous warning candidate from available sources.

    YOLO is kept as object recognition by default. It can label a selected
    motion/background candidate, but it does not trigger warnings by itself
    unless YOLO_USE_AS_WARNING_SOURCE is enabled in config.
    """
    candidates = []

    for detection in detections:
        if not has_detection(detection):
            continue

        if detection.get("source") == "yolo" and not config.YOLO_USE_AS_WARNING_SOURCE:
            continue

        candidates.append(detection)

    primary_detection = choose_primary_detection(
        candidates,
        frame_width,
        frame_height,
        frame_area,
    )

    return attach_yolo_recognition(
        primary_detection,
        recognition_detection,
        frame_width,
        frame_height,
    )


def make_display_detection(detection):
    if not has_detection(detection):
        return None

    display_detection = detection.copy()
    source = display_detection.get("source", "unknown")
    display_detection["is_final"] = True

    label = display_detection.get("label")
    if label:
        display_detection["display_label"] = f"FINAL {source} + {label}"
    else:
        display_detection["display_label"] = f"FINAL {source}"

    return display_detection


def make_recognition_display_detection(detection):
    if not has_detection(detection):
        return None

    display_detection = detection.copy()
    label = display_detection.get("label", "object")
    confidence = display_detection.get("confidence")

    if confidence is None:
        display_detection["display_label"] = f"YOLO {label}"
    else:
        display_detection["display_label"] = f"YOLO {label} {confidence:.2f}"

    return display_detection


class ContinuousDetectionPipeline:
    """
    Run background, frame-to-frame motion, and YOLO as one continuous guide loop.

    This replaces the older standby/walk split. The robot no longer has to decide
    which mode it is in before deciding what is dangerous.
    """

    def __init__(self, background_vision, yolo_vision=None):
        self.background_vision = background_vision
        self.yolo_vision = yolo_vision
        self.background_filter = DetectionPersistenceFilter()
        self.reset()

    def reset(self):
        self.background_filter.reset()
        self.last_background_detection = None
        self.last_background_detections = []
        self.last_background_mask = None
        self.last_motion_detection = None
        self.last_motion_detections = []

    def process(self, frame, frame_counter):
        height, width = frame.shape[:2]
        frame_area = height * width

        background_processed = False
        motion_processed = False

        if frame_counter % BACKGROUND_PROCESS_INTERVAL == 0:
            background_processed = True
            (
                self.last_background_detections,
                self.last_background_mask,
            ) = self.background_vision.detect_obstacles(frame)

            background_detection = choose_primary_detection(
                self.last_background_detections,
                width,
                height,
                frame_area,
            )
            self.last_background_detection = self.background_filter.update(
                background_detection,
                width,
                height,
            )

        if (
            MOTION_OBJECT_DETECTION_ENABLED
            and frame_counter % MOTION_OBJECT_PROCESS_INTERVAL == 0
        ):
            motion_processed = True
            (
                self.last_motion_detections,
                _,
            ) = self.background_vision.detect_moving_objects(frame)
            self.last_motion_detection = choose_primary_detection(
                self.last_motion_detections,
                width,
                height,
                frame_area,
            )

        yolo_detection = None
        if self.yolo_vision is not None:
            yolo_detection = self.yolo_vision.detect_object(frame)

        final_detection = combine_detections(
            width,
            height,
            frame_area,
            self.last_background_detection,
            self.last_motion_detection,
            yolo_detection,
            recognition_detection=yolo_detection,
        )

        return {
            "background_detection": self.last_background_detection,
            "background_detections": self.last_background_detections,
            "background_mask": self.last_background_mask,
            "background_processed": background_processed,
            "motion_detection": self.last_motion_detection,
            "motion_detections": self.last_motion_detections,
            "motion_processed": motion_processed,
            "yolo_detection": yolo_detection,
            "final_detection": final_detection,
        }
