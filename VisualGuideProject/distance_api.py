import math

from config import (
    CAMERA_HORIZONTAL_FOV_DEGREES,
    DISTANCE_ESTIMATION_ENABLED,
    DISTANCE_REFERENCE_WIDTH_M,
)


def estimate_distance_meters(detection, frame_width):
    """
    Estimate object distance from apparent bounding-box width.

    This is a monocular camera estimate, not a true depth measurement. It needs
    calibration for the real camera and the object type.
    """
    if not DISTANCE_ESTIMATION_ENABLED:
        return None

    if detection is None or detection.get("bbox") is None:
        return None

    _, _, box_width, _ = detection["bbox"]

    if box_width <= 0 or frame_width <= 0:
        return None

    fov_radians = math.radians(CAMERA_HORIZONTAL_FOV_DEGREES)

    if fov_radians <= 0:
        return None

    focal_length_pixels = frame_width / (2 * math.tan(fov_radians / 2))
    distance_meters = DISTANCE_REFERENCE_WIDTH_M * focal_length_pixels / box_width

    return max(0.0, distance_meters)


def format_distance(distance_meters):
    if distance_meters is None:
        return None

    if distance_meters >= 10:
        return f"{distance_meters:.0f} m"

    return f"{distance_meters:.1f} m"
