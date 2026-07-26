# guidance_api.py

import cv2
from config import (
    CLOSE_AREA_RATIO,
    MEDIUM_AREA_RATIO,
    REGION_GRID_COLS,
    REGION_GRID_ROWS,
)


def judge_region(detection, frame_width, frame_height):
    """
    Judge which grid region contains the object center.

    Default config is 3 x 3:
        top_left, top_center, top_right
        middle_left, middle_center, middle_right
        bottom_left, bottom_center, bottom_right
    """
    if detection is None or detection["center"] is None:
        return "clear"

    cx, cy = detection["center"]

    col_width = frame_width / REGION_GRID_COLS
    row_height = frame_height / REGION_GRID_ROWS

    col_index = min(REGION_GRID_COLS - 1, max(0, int(cx / col_width)))
    row_index = min(REGION_GRID_ROWS - 1, max(0, int(cy / row_height)))

    col_names = ["left", "center", "right"]
    row_names = ["top", "middle", "bottom"]

    col_name = col_names[col_index] if REGION_GRID_COLS == 3 else f"col{col_index + 1}"
    row_name = row_names[row_index] if REGION_GRID_ROWS == 3 else f"row{row_index + 1}"

    return f"{row_name}_{col_name}"


def judge_direction(detection, frame_width):
    """
    Judge left / center / right based on object center.
    """
    if detection is None or detection["center"] is None:
        return "clear"

    cx, _ = detection["center"]

    left_boundary = frame_width // 3
    right_boundary = 2 * frame_width // 3

    if cx < left_boundary:
        return "left"
    elif cx > right_boundary:
        return "right"
    else:
        return "center"


def estimate_closeness(detection, frame_area):
    """
    Estimate rough closeness based on object size in image.

    This is NOT true distance measurement.
    """
    if detection is None or detection["bbox"] is None:
        return "none"

    area_ratio = detection["box_area"] / frame_area

    if area_ratio >= CLOSE_AREA_RATIO:
        return "close"
    elif area_ratio >= MEDIUM_AREA_RATIO:
        return "medium"
    else:
        return "far"


def draw_regions(frame):
    """
    Draw the configured guide regions.
    """
    height, width = frame.shape[:2]

    for col_index in range(1, REGION_GRID_COLS):
        x = int(width * col_index / REGION_GRID_COLS)
        cv2.line(frame, (x, 0), (x, height), (255, 0, 0), 2)

    for row_index in range(1, REGION_GRID_ROWS):
        y = int(height * row_index / REGION_GRID_ROWS)
        cv2.line(frame, (0, y), (width, y), (255, 0, 0), 2)

    if REGION_GRID_COLS == 3 and REGION_GRID_ROWS == 3:
        labels = (
            ("TOP L", 10, 25),
            ("TOP C", width // 3 + 10, 25),
            ("TOP R", 2 * width // 3 + 10, 25),
            ("MID L", 10, height // 3 + 25),
            ("MID C", width // 3 + 10, height // 3 + 25),
            ("MID R", 2 * width // 3 + 10, height // 3 + 25),
            ("BOT L", 10, 2 * height // 3 + 25),
            ("BOT C", width // 3 + 10, 2 * height // 3 + 25),
            ("BOT R", 2 * width // 3 + 10, 2 * height // 3 + 25),
        )

        for label, x, y in labels:
            cv2.putText(
                frame,
                label,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 0, 0),
                1,
            )

def draw_detections(frame, detections):
    """
    Draw multiple detected objects.
    """

    if not detections:
        return frame

    for index, detection in enumerate(detections):
        if detection is None or detection.get("bbox") is None:
            continue

        x, y, w, h = detection["bbox"]
        cx, cy = detection["center"]

        source = detection.get("source")
        color = (0, 255, 0)

        if detection.get("is_final"):
            color = (0, 255, 255)
        elif source == "motion":
            color = (0, 165, 255)
        elif source == "yolo":
            color = (255, 0, 255)

        # Draw bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        # Draw center point
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        # Draw object number
        cv2.putText(
            frame,
            detection.get("display_label", f"Obj {index + 1}"),
            (x, max(15, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    return frame
