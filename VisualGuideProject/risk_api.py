# risk_api.py

import math
from collections import deque

from config import (
    APPROACH_RISK_DISTANCE_DROP_RATIO,
    APPROACH_RISK_ENABLED,
    APPROACH_RISK_FAST_SPEED_RATIO,
    APPROACH_RISK_HIGH_SCORE,
    APPROACH_RISK_HISTORY_FRAMES,
    APPROACH_RISK_MEDIUM_SCORE,
    APPROACH_RISK_MIN_AREA_GROWTH,
    APPROACH_RISK_STRONG_AREA_GROWTH,
)


_ROW_INDEX = {"top": 0, "middle": 1, "bottom": 2}
_COL_INDEX = {"left": 0, "center": 1, "right": 2}


def _has_detection(detection):
    return detection is not None and detection.get("bbox") is not None


def _empty_risk():
    return {
        "level": "none",
        "score": 0,
        "reasons": [],
        "area_growth_ratio": 0.0,
        "distance_drop_ratio": 0.0,
        "speed_ratio": 0.0,
        "distance_grade": "unknown",
    }


def _parse_region(region):
    if not region or region == "clear" or "_" not in region:
        return None, None

    row_name, col_name = region.split("_", 1)
    return _ROW_INDEX.get(row_name), _COL_INDEX.get(col_name)


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


def _distance_grade(distance_m):
    if distance_m is None:
        return "unknown"

    if distance_m <= 1.0:
        return "near"

    if distance_m <= 2.0:
        return "medium"

    return "far"


def format_risk(risk):
    if not risk or risk.get("level") == "none":
        return "none"

    reasons = ",".join(risk.get("reasons", [])[:3])
    return f"{risk['level']}:{risk['score']} {reasons}"


class ApproachRiskTracker:
    """
    Grade whether the selected object is approaching the user.

    This does not try to turn a single camera into a true depth sensor. It looks
    for useful trends:

    - side region moving toward center
    - top/middle moving downward in the image
    - bounding box getting larger
    - rough distance estimate decreasing
    - center moving quickly

    Random left-to-right motion without size/distance growth is intentionally
    capped to low risk.
    """

    def __init__(self, history_frames=APPROACH_RISK_HISTORY_FRAMES):
        self.history = deque(maxlen=max(2, history_frames))

    def reset(self):
        self.history.clear()

    def update(
        self,
        detection,
        frame_width,
        frame_height,
        frame_counter,
        region=None,
        distance_m=None,
    ):
        if not APPROACH_RISK_ENABLED:
            return _empty_risk()

        if not _has_detection(detection):
            self.reset()
            return _empty_risk()

        observation = self._make_observation(
            detection,
            frame_width,
            frame_height,
            frame_counter,
            region,
            distance_m,
        )

        if self.history and not self._matches_previous_target(observation):
            self.history.clear()

        self.history.append(observation)

        if len(self.history) < 2:
            return _empty_risk()

        return self._grade_current_track(frame_width, frame_height)

    def _make_observation(
        self,
        detection,
        frame_width,
        frame_height,
        frame_counter,
        region,
        distance_m,
    ):
        bbox = detection["bbox"]
        center = detection["center"]
        frame_area = frame_width * frame_height
        box_area = detection.get("box_area", bbox[2] * bbox[3])
        area_ratio = detection.get("area_ratio")

        if area_ratio is None:
            area_ratio = box_area / frame_area if frame_area else 0.0

        return {
            "bbox": bbox,
            "center": center,
            "frame": frame_counter,
            "region": region,
            "row_index": _parse_region(region)[0],
            "col_index": _parse_region(region)[1],
            "area_ratio": area_ratio,
            "distance_m": distance_m,
            "distance_grade": _distance_grade(distance_m),
        }

    def _matches_previous_target(self, observation):
        previous = self.history[-1]

        if _box_iou(previous["bbox"], observation["bbox"]) >= 0.08:
            return True

        frame_delta = max(1, observation["frame"] - previous["frame"])
        distance = _center_distance(previous["center"], observation["center"])

        # Allow fast motion, but reset if the selected object jumps too far to
        # plausibly be the same target.
        return distance / frame_delta <= 90

    def _grade_current_track(self, frame_width, frame_height):
        first = self.history[0]
        previous = self.history[-2]
        current = self.history[-1]

        frame_delta = max(1, current["frame"] - previous["frame"])
        frame_diagonal = math.hypot(frame_width, frame_height)

        first_area = max(first["area_ratio"], 0.0001)
        current_area = current["area_ratio"]
        area_growth_ratio = (current_area - first_area) / first_area

        distance_drop_ratio = 0.0
        if first["distance_m"] and current["distance_m"]:
            distance_drop_ratio = (
                first["distance_m"] - current["distance_m"]
            ) / first["distance_m"]

        speed_ratio = (
            _center_distance(previous["center"], current["center"])
            / frame_diagonal
            / frame_delta
        )

        score = 0
        reasons = []

        has_size_or_distance_growth = (
            area_growth_ratio >= APPROACH_RISK_MIN_AREA_GROWTH
            or distance_drop_ratio >= APPROACH_RISK_DISTANCE_DROP_RATIO
        )

        if area_growth_ratio >= APPROACH_RISK_STRONG_AREA_GROWTH:
            score += 2
            reasons.append("size_growing_fast")
        elif area_growth_ratio >= APPROACH_RISK_MIN_AREA_GROWTH:
            score += 1
            reasons.append("size_growing")

        if distance_drop_ratio >= APPROACH_RISK_DISTANCE_DROP_RATIO:
            score += 1
            reasons.append("distance_decreasing")

        if speed_ratio >= APPROACH_RISK_FAST_SPEED_RATIO:
            score += 1
            reasons.append("fast_motion")

        side_to_center = (
            first["col_index"] in (0, 2)
            and current["col_index"] == 1
        )
        top_to_lower = (
            first["row_index"] is not None
            and current["row_index"] is not None
            and current["row_index"] > first["row_index"]
        )

        first_center_offset = abs(first["center"][0] - frame_width / 2)
        current_center_offset = abs(current["center"][0] - frame_width / 2)
        moving_toward_center = current_center_offset < first_center_offset * 0.75

        if side_to_center and has_size_or_distance_growth:
            score += 2
            reasons.append("side_to_center")
        elif side_to_center:
            reasons.append("side_cross_no_growth")

        if top_to_lower and has_size_or_distance_growth:
            score += 2
            reasons.append("top_to_lower")
        elif top_to_lower:
            reasons.append("downward_no_growth")

        if moving_toward_center and has_size_or_distance_growth:
            score += 1
            reasons.append("toward_center")

        if current["distance_grade"] == "near" and has_size_or_distance_growth:
            score += 1
            reasons.append("near_grade")

        # A quick lateral crossing is not enough. Without growth/decreasing
        # distance, cap the risk so random side-to-side traffic does not shout.
        if not has_size_or_distance_growth:
            score = min(score, 1)

        if score >= APPROACH_RISK_HIGH_SCORE:
            level = "high"
        elif score >= APPROACH_RISK_MEDIUM_SCORE:
            level = "medium"
        elif score > 0:
            level = "low"
        else:
            level = "none"

        return {
            "level": level,
            "score": score,
            "reasons": reasons,
            "area_growth_ratio": area_growth_ratio,
            "distance_drop_ratio": distance_drop_ratio,
            "speed_ratio": speed_ratio,
            "distance_grade": current["distance_grade"],
        }
