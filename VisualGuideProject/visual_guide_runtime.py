# visual_guide_runtime.py

import cv2

from background_api import BackgroundCaptureCancelled, capture_stable_background
from camera_api import CameraAPI
from config import (
    GUIDE_MODE,
    SHOW_ALL_DETECTION_SOURCES,
    SHOW_DEBUG_WINDOWS,
    SHOW_DETECTION_MASK,
)
from detection_api import (
    ContinuousDetectionPipeline,
    has_detection,
    make_display_detection,
    make_recognition_display_detection,
)
from distance_api import estimate_distance_meters, format_distance
from guidance_api import (
    draw_detections,
    draw_regions,
    estimate_closeness,
    judge_direction,
    judge_region,
)
from motion_api import MotionAPI
from output_api import output_warning
from risk_api import ApproachRiskTracker, format_risk
from stability_api import DetectionStabilizer
from vision_api import VisionAPI
from warning_api import make_warning
from yolo_vision_api import YOLOVisionAPI


SESSION_USER_QUIT = "user_quit"
SESSION_CAMERA_LOST = "camera_lost"
SESSION_CANCELLED = "cancelled"
SESSION_ERROR = "error"


def run_visual_guide_session(
    camera_index=None,
    window_name="Visual Guide Robot",
    show_debug_windows=SHOW_DEBUG_WINDOWS,
):
    """
    Run one continuous visual-guide session.

    This function has no time limit. It returns when:

    - user presses q
    - camera cannot start
    - camera is unplugged / frame read fails
    - background capture is cancelled
    """
    camera = CameraAPI(camera_index=camera_index) if camera_index is not None else CameraAPI()
    background_vision = VisionAPI()
    yolo_vision = YOLOVisionAPI()
    motion_api = MotionAPI()
    detection_pipeline = ContinuousDetectionPipeline(background_vision, yolo_vision)
    stabilizer = DetectionStabilizer()
    risk_tracker = ApproachRiskTracker()

    frame_counter = 0
    current_mode = GUIDE_MODE

    try:
        camera.start()

        print("Visual Guide Robot Started.")
        print("Mode: continuous guide.")
        print("Keep camera view empty while background is captured.")
        print("Press q to quit this program.")

        capture_stable_background(camera, background_vision)
        detection_pipeline.reset()
        risk_tracker.reset()

        output_warning("Guide mode.", mode="both", interrupt=True)

        while True:
            frame_counter += 1

            frame = camera.get_frame()
            height, width = frame.shape[:2]
            frame_area = height * width

            motion_score = motion_api.estimate_motion(frame)

            detection_state = detection_pipeline.process(frame, frame_counter)
            background_detections = detection_state["background_detections"]
            background_mask = detection_state["background_mask"]
            motion_detections = detection_state["motion_detections"]
            yolo_detection = detection_state["yolo_detection"]
            final_detection = detection_state["final_detection"]

            final_detection = stabilizer.stabilize_detection(
                final_detection,
                width,
                height,
            )

            direction = judge_direction(final_detection, width)
            region = judge_region(final_detection, width, height)
            closeness = estimate_closeness(final_detection, frame_area)
            distance_m = estimate_distance_meters(final_detection, width)
            risk = risk_tracker.update(
                final_detection,
                width,
                height,
                frame_counter,
                region=region,
                distance_m=distance_m,
            )

            label = None
            if final_detection is not None:
                label = final_detection.get("label")
                final_detection["region"] = region
                final_detection["approach_risk"] = risk

                if distance_m is not None:
                    final_detection["distance_m"] = distance_m

            raw_warning = make_warning(
                direction=direction,
                closeness=closeness,
                label=label,
                mode=current_mode,
                distance_m=distance_m,
                risk_level=risk["level"],
            )
            warning = stabilizer.stabilize_warning(raw_warning)

            output_warning(warning, interrupt=True)

            if show_debug_windows:
                _draw_runtime_overlay(
                    frame=frame,
                    background_detections=background_detections,
                    motion_detections=motion_detections,
                    yolo_detection=yolo_detection,
                    final_detection=final_detection,
                    current_mode=current_mode,
                    motion_score=motion_score,
                    region=region,
                    distance_m=distance_m,
                    risk=risk,
                )

                cv2.imshow(window_name, frame)

                if SHOW_DETECTION_MASK and background_mask is not None:
                    cv2.imshow("Detection Mask", background_mask)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    return SESSION_USER_QUIT

    except BackgroundCaptureCancelled:
        print("Visual Guide session cancelled during background capture.")
        return SESSION_CANCELLED

    except RuntimeError as error:
        print(f"Visual Guide session stopped: {error}")
        return SESSION_CAMERA_LOST

    except KeyboardInterrupt:
        raise

    except Exception as error:
        print(f"Visual Guide session error: {error}")
        return SESSION_ERROR

    finally:
        camera.stop()
        cv2.destroyAllWindows()


def _draw_runtime_overlay(
    frame,
    background_detections,
    motion_detections,
    yolo_detection,
    final_detection,
    current_mode,
    motion_score,
    region,
    distance_m,
    risk,
):
    draw_regions(frame)

    if SHOW_ALL_DETECTION_SOURCES:
        debug_detections = background_detections + motion_detections

        if has_detection(yolo_detection):
            debug_detections.append(yolo_detection)
    else:
        final_display_detection = make_display_detection(final_detection)
        recognition_display_detection = make_recognition_display_detection(
            yolo_detection
        )
        debug_detections = []

        if final_display_detection is not None:
            debug_detections.append(final_display_detection)

        if (
            recognition_display_detection is not None
            and (
                final_detection is None
                or final_detection.get("recognized_by") != "yolo"
            )
        ):
            debug_detections.append(recognition_display_detection)

    draw_detections(frame, debug_detections)

    cv2.putText(
        frame,
        f"Mode: {current_mode} | Motion: {motion_score:.3f}",
        (20, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )

    recognition_label = None
    recognition_confidence = None

    if final_detection is not None and final_detection.get("label"):
        recognition_label = final_detection.get("label")
        recognition_confidence = final_detection.get("confidence")
    elif has_detection(yolo_detection):
        recognition_label = yolo_detection.get("label")
        recognition_confidence = yolo_detection.get("confidence")

    if recognition_label:
        confidence_text = ""
        if recognition_confidence is not None:
            confidence_text = f" {recognition_confidence:.2f}"

        cv2.putText(
            frame,
            f"YOLO recognition: {recognition_label}{confidence_text}",
            (20, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

    distance_text = format_distance(distance_m)
    risk_text = format_risk(risk)
    if final_detection is not None:
        cv2.putText(
            frame,
            (
                f"Region: {region} | Distance: {distance_text or 'n/a'} | "
                f"Source: {final_detection.get('source')}"
            ),
            (20, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Risk: {risk_text}",
            (20, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
        )
