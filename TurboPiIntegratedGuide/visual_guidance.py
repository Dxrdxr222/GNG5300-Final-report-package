from typing import Mapping, Optional


TURN_LEFT = "left"
TURN_RIGHT = "right"


def recommend_turn_away_from_detection(
    detection: Optional[Mapping],
    frame_width: int,
) -> Optional[str]:
    """Convert the existing visual-guide detection shape into a turn hint.

    Vision is advisory only. None means that the avoidance controller should
    use its deterministic alternating fallback.
    """
    if not detection or frame_width <= 0:
        return None

    center = detection.get("center")
    if not center or len(center) < 2:
        return None

    center_x = float(center[0])
    left_boundary = frame_width / 3.0
    right_boundary = 2.0 * frame_width / 3.0

    if center_x < left_boundary:
        return TURN_RIGHT
    if center_x > right_boundary:
        return TURN_LEFT
    return None

