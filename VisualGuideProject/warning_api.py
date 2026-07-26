# warning_api.py

from config import INCLUDE_DISTANCE_IN_WARNING


def _distance_phrase(distance_m):
    if not INCLUDE_DISTANCE_IN_WARNING or distance_m is None:
        return ""

    if distance_m >= 10:
        return f" About {distance_m:.0f} meters."

    return f" About {distance_m:.1f} meters."


def make_warning(
    direction,
    closeness,
    label=None,
    mode=None,
    distance_m=None,
    risk_level=None,
):
    """
    Convert direction + closeness into a useful warning message.

    label:
        Optional object name from YOLO, such as person, chair, backpack.

    risk_level:
        Optional approach-risk grade from risk_api. This can upgrade a far object
        to a caution warning when its motion/size trend suggests it is coming
        toward the user.
    """

    if direction == "clear" or closeness == "none":
        return None

    approaching = risk_level in ("medium", "high")

    if closeness == "far" and approaching:
        closeness = "medium"
    elif closeness == "far":
        return None

    if label:
        object_name = label
    else:
        object_name = "obstacle"

    distance_text = _distance_phrase(distance_m)

    if approaching and closeness == "close" and direction == "center":
        return f"Stop. approaching {object_name} ahead.{distance_text}"

    if approaching and closeness == "medium":
        if direction == "center":
            return f"Caution. approaching {object_name} ahead.{distance_text}"

        if direction == "left":
            return f"Caution. approaching {object_name} from left."

        if direction == "right":
            return f"Caution. approaching {object_name} from right."

    if closeness == "close" and direction == "center":
        return f"Stop. {object_name} ahead.{distance_text}"

    if closeness == "close" and direction == "left":
        return f"{object_name} on left."

    if closeness == "close" and direction == "right":
        return f"{object_name} on right."

    if closeness == "medium" and direction == "center":
        return f"Caution. {object_name} ahead.{distance_text}"

    if closeness == "medium" and direction == "left":
        return f"Caution. {object_name} on left."

    if closeness == "medium" and direction == "right":
        return f"Caution. {object_name} on right."

    return None
