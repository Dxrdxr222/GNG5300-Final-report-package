import argparse
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path


def _restart_with_project_venv_if_needed():
    """
    On the Windows laptop, always run this test with the project venv when it
    exists. This prevents YOLO from failing just because the terminal selected
    a Python environment without ultralytics installed.
    """
    try:
        import config as runtime_config

        if os.name != "nt":
            return

        if not getattr(runtime_config, "WINDOWS_PROJECT_VENV_ENABLED", True):
            return

        project_dir = Path(__file__).resolve().parent
        project_python = project_dir / getattr(
            runtime_config,
            "WINDOWS_PROJECT_VENV_PYTHON",
            ".venv-win\\Scripts\\python.exe",
        )

        if not project_python.exists():
            return

        current_python = Path(sys.executable).resolve()
        target_python = project_python.resolve()

        if str(current_python).lower() == str(target_python).lower():
            return

        if os.environ.get("VISUAL_GUIDE_PROJECT_VENV_RESTARTED") == "1":
            return

        os.environ["VISUAL_GUIDE_PROJECT_VENV_RESTARTED"] = "1"
        print(
            f"LIVE TEST: restarting with project Python: {target_python}",
            flush=True,
        )
        os.execv(str(target_python), [str(target_python), *sys.argv])

    except Exception as error:
        print(f"LIVE TEST: could not switch to project Python automatically: {error}")
        print(f"LIVE TEST: continuing with current Python: {sys.executable}")


_restart_with_project_venv_if_needed()

import cv2

from background_api import BackgroundCaptureCancelled, capture_stable_background
from camera_api import CameraAPI
from config import (
    AUDIO_ENABLED,
    AUDIO_OUTPUT_MODE,
    BACKGROUND_CAPTURE_FRAMES,
    GUIDE_MODE,
    SHOW_ALL_DETECTION_SOURCES,
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
from output_api import classify_beep_pattern, output_warning, set_audio_override
from risk_api import ApproachRiskTracker, format_risk
from stability_api import DetectionStabilizer
from vision_api import VisionAPI
from warning_api import make_warning
from yolo_vision_api import YOLOVisionAPI


TEST_SECONDS = 100
BACKGROUND_WAIT_SECONDS = 4
SHOW_CAMERA_WINDOW = True
WINDOW_NAME = "Visual Guide Live Test"
TEST_LOG_PATH = Path("TEST_LOG.md")


def _format_counter(counter, limit=5):
    if not counter:
        return "none"

    return ", ".join(
        f"{name}: {count}" for name, count in counter.most_common(limit)
    )


def _format_ms(value):
    if value is None:
        return "n/a"

    return f"{value:.1f} ms"


def _ensure_test_log():
    if TEST_LOG_PATH.exists():
        return

    TEST_LOG_PATH.write_text(
        "# Visual Guide Test Log\n\n"
        "This file records each real camera test, what we noticed, and what "
        "should be optimized next.\n\n",
        encoding="utf-8",
    )


def _append_test_log(summary):
    _ensure_test_log()

    observations = []
    optimizations = []

    if summary["motion_hits"] > summary["background_hits"]:
        observations.append(
            "Frame-to-frame motion detection was the strongest signal in this run."
        )

    if summary["warning_frames"] > summary["frames"] * 0.6:
        observations.append(
            "Warnings appeared on most frames, so the detector is sensitive."
        )
        optimizations.append(
            "Add smoothing/hysteresis so warnings do not feel jumpy."
        )

    if summary["raw_warning_changes"] > summary["warning_changes"]:
        observations.append(
            "The stabilizer reduced warning changes compared with raw detection."
        )

    if summary["warning_changes"] > 12:
        observations.append(
            "Stabilized warning text still changed often during the run."
        )
        optimizations.append(
            "Tune stabilizer settings and motion sensitivity further."
        )

    risky_frames = (
        summary["risk_counts"].get("medium", 0)
        + summary["risk_counts"].get("high", 0)
    )
    if risky_frames > 0:
        observations.append(
            "Approach-risk grading detected medium/high risk movement trends."
        )

    if summary["fps"] < 5:
        observations.append(
            "Test throughput was below 5 FPS, so this run is not valid for detector comparison."
        )
        optimizations.append(
            "Rerun after restarting/replugging the camera, or compare with a no-window test."
        )
    elif summary["fps"] < 15:
        observations.append(
            "Diagnostic display and printing reduce test FPS; real app speed may be higher."
        )

    if summary["distance_seen"]:
        observations.append(
            "Approximate distance values were produced, but they still need calibration."
        )
        optimizations.append(
            "Calibrate distance with a known object at known distances."
        )

    if summary["audio_output_active"]:
        observations.append(
            f"Audio output was active through {summary['audio_source']}."
        )
    else:
        observations.append("Audio output was inactive for this run.")

    if summary["audio_output_active"] and AUDIO_OUTPUT_MODE.lower() == "beep":
        if summary["beep_candidate_frames"] > 0:
            observations.append(
                "Some stable warnings matched the beep policy."
            )
        else:
            observations.append(
                "No stable warning matched the beep policy, so no beep was expected."
            )

    yolo_stats = summary["yolo_stats"]
    if yolo_stats["config_enabled"] and yolo_stats["enabled"]:
        observations.append(
            "YOLO was enabled; compare YOLO inference timing against total camera FPS."
        )

        if yolo_stats["average_inference_ms"] and yolo_stats["average_inference_ms"] > 150:
            optimizations.append(
                "YOLO inference is slow; increase YOLO_PROCESS_INTERVAL or use an exported edge format."
            )
    elif yolo_stats["config_enabled"] and not yolo_stats["enabled"]:
        observations.append(
            "YOLO was requested by config.py, but it could not become active."
        )
        optimizations.append(
            f"Fix YOLO load error: {yolo_stats['last_error'] or 'unknown error'}"
        )
    else:
        observations.append("YOLO was disabled by config.py for this run.")

    if not observations:
        observations.append("No major issue was obvious from automatic metrics.")

    if not optimizations:
        optimizations.append("Review the camera window and decide the next tuning target.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = [
        f"## {timestamp} - Live camera test",
        "",
        f"- Duration: {summary['elapsed']:.1f}s",
        f"- Camera index: {summary['camera_index']}",
        f"- Camera reported size: {summary['camera_width']} x {summary['camera_height']}",
        f"- Processing size: {summary['processing_width']} x {summary['processing_height']}",
        f"- Camera FPS reported: {summary['camera_fps']:.1f}",
        f"- Audio output active: {summary['audio_output_active']}",
        f"- Audio source: {summary['audio_source']}",
        f"- Beep candidate frames: {summary['beep_candidate_frames']}",
        f"- Beep candidate patterns: {_format_counter(summary['beep_pattern_counts'])}",
        f"- Background settle seconds: {summary['background_settle_seconds']:.1f}",
        f"- Background capture frames: {summary['background_capture_frames']}",
        f"- Frames: {summary['frames']}",
        f"- Approx FPS: {summary['fps']:.1f}",
        f"- Background detection frames: {summary['background_hits']}",
        f"- Motion detection frames: {summary['motion_hits']}",
        f"- Raw warning frames: {summary['raw_warning_hits']}",
        f"- Warning frames: {summary['warning_frames']}",
        f"- Raw warning changes: {summary['raw_warning_changes']}",
        f"- Warning changes: {summary['warning_changes']}",
        f"- Modes: {_format_counter(summary['mode_counts'])}",
        f"- Sources: {_format_counter(summary['source_counts'])}",
        f"- Regions: {_format_counter(summary['region_counts'])}",
        f"- Closeness: {_format_counter(summary['closeness_counts'])}",
        f"- Risk levels: {_format_counter(summary['risk_counts'])}",
        f"- YOLO requested by config: {summary['yolo_stats']['config_enabled']}",
        f"- YOLO active: {summary['yolo_stats']['enabled']}",
        f"- YOLO config file: {summary['yolo_stats']['config_path']}",
        f"- YOLO Python executable: {summary['yolo_stats']['python_executable']}",
        f"- YOLO model path: {summary['yolo_stats']['model_path']}",
        f"- YOLO confidence: {summary['yolo_stats']['confidence']}",
        f"- YOLO process interval: {summary['yolo_stats']['process_interval']}",
        f"- YOLO allowlist: {summary['yolo_stats']['allowlist']}",
        f"- YOLO detection frames: {summary['yolo_hits']}",
        f"- YOLO final frames: {summary['yolo_final_hits']}",
        f"- YOLO inference runs: {summary['yolo_stats']['inference_runs']}",
        f"- YOLO inference hits: {summary['yolo_stats']['inference_hits']}",
        f"- YOLO cached returns: {summary['yolo_stats']['cached_returns']}",
        f"- YOLO labels: {_format_counter(summary['yolo_label_counts'])}",
        f"- YOLO avg inference: {_format_ms(summary['yolo_stats']['average_inference_ms'])}",
        f"- YOLO last inference: {_format_ms(summary['yolo_stats']['last_inference_ms'])}",
        f"- YOLO last error: {summary['yolo_stats']['last_error'] or 'none'}",
        "",
        "What we noticed:",
    ]

    log_entry.extend(f"- {item}" for item in observations)
    log_entry.append("")
    log_entry.append("Need to optimize:")
    log_entry.extend(f"- {item}" for item in optimizations)
    log_entry.append("")

    with TEST_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write("\n".join(log_entry))
        log_file.write("\n")


def _draw_test_overlay(frame, data):
    draw_regions(frame)
    draw_detections(frame, data["debug_detections"])

    cv2.putText(
        frame,
        f"Mode: {data['mode']} | Motion: {data['motion_score']:.3f}",
        (10, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        (
            f"Source: {data['source']} | Region: {data['region']} | "
            f"Close: {data['closeness']} | Dist: {data['distance_text']}"
        ),
        (10, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 255, 255),
        1,
    )

    cv2.putText(
        frame,
        f"Risk: {data['risk_text']}",
        (10, 67),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 255, 255),
        1,
    )

    if data["recognition_text"]:
        cv2.putText(
            frame,
            data["recognition_text"],
            (10, 89),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 0, 255),
            1,
        )

    warning = data["warning"] or "No warning"
    cv2.putText(
        frame,
        warning,
        (10, frame.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 255) if data["warning"] else (0, 255, 0),
        2,
    )

    cv2.putText(
        frame,
        "Press q to end test",
        (10, frame.shape[0] - 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
    )


def _draw_background_capture_preview(frame, phase, remaining_seconds, frame_index, frame_count):
    if phase == "settling":
        message = f"Keep view empty: {remaining_seconds:.1f}s"
    else:
        message = f"Capturing background: {frame_index}/{frame_count}"

    cv2.putText(
        frame,
        message,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        "Press q to cancel",
        (10, frame.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )


def run_test(
    camera_index=None,
    test_seconds=TEST_SECONDS,
    background_wait_seconds=BACKGROUND_WAIT_SECONDS,
    show_window=SHOW_CAMERA_WINDOW,
    audio_enabled=False,
):
    camera = CameraAPI(camera_index=camera_index) if camera_index is not None else CameraAPI()
    vision = VisionAPI()
    yolo_vision = YOLOVisionAPI()
    motion_api = MotionAPI()
    detection_pipeline = ContinuousDetectionPipeline(vision, yolo_vision)
    stabilizer = DetectionStabilizer()
    risk_tracker = ApproachRiskTracker()
    current_mode = GUIDE_MODE

    background_hits = 0
    motion_hits = 0
    warning_hits = 0
    frames = 0
    last_print = 0
    last_warning = None
    last_raw_warning = None
    last_background_detections = []
    last_motion_detections = []
    warning_changes = 0
    raw_warning_changes = 0
    raw_warning_hits = 0
    yolo_hits = 0
    yolo_final_hits = 0
    yolo_label_counts = Counter()
    mode_counts = Counter()
    source_counts = Counter()
    region_counts = Counter()
    closeness_counts = Counter()
    risk_counts = Counter()
    distance_seen = False
    beep_candidate_frames = 0
    beep_pattern_counts = Counter()
    audio_output_active = bool(audio_enabled or AUDIO_ENABLED)
    audio_source = "forced by --audio" if audio_enabled else (
        "config.py" if AUDIO_ENABLED else "off"
    )

    if audio_enabled:
        set_audio_override(True)
        print("LIVE TEST: temporary audio beep output enabled.")
    else:
        set_audio_override(None)

    print(
        f"LIVE TEST: audio output active = {audio_output_active} "
        f"({audio_source}, mode={AUDIO_OUTPUT_MODE})"
    )
    print(f"LIVE TEST: Python executable = {sys.executable}")

    print("LIVE TEST: opening camera...")
    camera.start()
    actual_width = int(camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = camera.cap.get(cv2.CAP_PROP_FPS)

    try:
        print(f"LIVE TEST: camera index = {camera.camera_index}")
        print(
            f"LIVE TEST: keep view empty for {background_wait_seconds} seconds, "
            f"then {BACKGROUND_CAPTURE_FRAMES} background frames..."
        )

        def progress_callback(
            frame,
            phase,
            remaining_seconds,
            frame_index,
            frame_count,
        ):
            if not show_window:
                return True

            preview = frame.copy()
            _draw_background_capture_preview(
                preview,
                phase,
                remaining_seconds,
                frame_index,
                frame_count,
            )
            cv2.imshow(WINDOW_NAME, preview)

            return (cv2.waitKey(1) & 0xFF) != ord("q")

        try:
            frame = capture_stable_background(
                camera,
                vision,
                settle_seconds=background_wait_seconds,
                progress_callback=progress_callback,
            )
        except BackgroundCaptureCancelled:
            print("LIVE TEST: cancelled before background capture.")
            return

        detection_pipeline.reset()
        risk_tracker.reset()
        processing_height, processing_width = frame.shape[:2]
        print("LIVE TEST: background captured. Move your face/object now.")
        start = time.monotonic()

        while time.monotonic() - start < test_seconds:
            frames += 1
            frame = camera.get_frame()
            height, width = frame.shape[:2]
            frame_area = height * width

            motion_score = motion_api.estimate_motion(frame)
            detection_state = detection_pipeline.process(frame, frames)
            background_detection = detection_state["background_detection"]
            motion_detection = detection_state["motion_detection"]
            yolo_detection = detection_state["yolo_detection"]
            last_background_detections = detection_state["background_detections"]
            last_motion_detections = detection_state["motion_detections"]
            final_detection = detection_state["final_detection"]

            if detection_state["background_processed"] and has_detection(
                background_detection
            ):
                background_hits += 1

            if detection_state["motion_processed"] and has_detection(motion_detection):
                motion_hits += 1

            if has_detection(yolo_detection):
                yolo_hits += 1
                if yolo_detection.get("label"):
                    yolo_label_counts[yolo_detection["label"]] += 1

            final_detection = stabilizer.stabilize_detection(
                final_detection,
                width,
                height,
            )

            direction = judge_direction(final_detection, width)
            region = judge_region(final_detection, width, height)
            closeness = estimate_closeness(final_detection, frame_area)
            distance_m = estimate_distance_meters(final_detection, width)
            label = final_detection.get("label") if final_detection else None
            risk = risk_tracker.update(
                final_detection,
                width,
                height,
                frames,
                region=region,
                distance_m=distance_m,
            )

            if final_detection is not None:
                final_detection["approach_risk"] = risk

            raw_warning = make_warning(
                direction=direction,
                closeness=closeness,
                label=label,
                mode=current_mode,
                distance_m=distance_m,
                risk_level=risk["level"],
            )
            warning = stabilizer.stabilize_warning(raw_warning)

            beep_pattern = None
            if AUDIO_OUTPUT_MODE.lower() == "beep":
                beep_pattern = classify_beep_pattern(warning)

            if beep_pattern is not None:
                beep_candidate_frames += 1
                beep_pattern_counts[beep_pattern] += 1

            if audio_output_active:
                output_warning(warning, interrupt=True)

            if raw_warning:
                raw_warning_hits += 1

            if warning:
                warning_hits += 1

            if warning != last_warning and last_warning is not None:
                warning_changes += 1

            if raw_warning != last_raw_warning and last_raw_warning is not None:
                raw_warning_changes += 1

            source = final_detection.get("source") if final_detection else "none"
            bbox = final_detection.get("bbox") if final_detection else None
            distance_text = format_distance(distance_m) or "n/a"
            risk_text = format_risk(risk)
            recognition_label = None
            recognition_confidence = None

            if final_detection is not None and final_detection.get("label"):
                recognition_label = final_detection.get("label")
                recognition_confidence = final_detection.get("confidence")
            elif has_detection(yolo_detection):
                recognition_label = yolo_detection.get("label")
                recognition_confidence = yolo_detection.get("confidence")

            recognition_text = None
            if recognition_label:
                if recognition_confidence is None:
                    recognition_text = f"YOLO recognition: {recognition_label}"
                else:
                    recognition_text = (
                        f"YOLO recognition: {recognition_label} "
                        f"{recognition_confidence:.2f}"
                    )

            if source == "yolo":
                yolo_final_hits += 1

            if distance_m is not None:
                distance_seen = True

            mode_counts[current_mode] += 1
            source_counts[source] += 1
            region_counts[region] += 1
            closeness_counts[closeness] += 1
            risk_counts[risk["level"]] += 1

            if show_window:
                display_frame = frame.copy()
                if SHOW_ALL_DETECTION_SOURCES:
                    debug_detections = last_background_detections + last_motion_detections

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

                _draw_test_overlay(
                    display_frame,
                    {
                        "debug_detections": debug_detections,
                        "mode": current_mode,
                        "motion_score": motion_score,
                        "source": source,
                        "region": region,
                        "closeness": closeness,
                        "distance_text": distance_text,
                        "risk_text": risk_text,
                        "recognition_text": recognition_text,
                        "warning": warning,
                    },
                )
                cv2.imshow(WINDOW_NAME, display_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("LIVE TEST: stopped early by user.")
                    break

            now = time.monotonic()
            if (
                now - last_print >= 0.75
                or warning != last_warning
                or raw_warning != last_raw_warning
            ):
                print(
                    f"t={now - start:05.1f}s mode={current_mode:<7} "
                    f"motion={motion_score:.3f} source={source:<10} "
                    f"region={region:<13} close={closeness:<6} "
                    f"dist={distance_text:<5} risk={risk_text:<24} bbox={bbox} "
                    f"recog={recognition_label or 'none'} "
                    f"raw={raw_warning} stable={warning}"
                )
                last_print = now
                last_warning = warning
                last_raw_warning = raw_warning

        elapsed = time.monotonic() - start
        fps = frames / elapsed if elapsed > 0 else 0
        print("LIVE TEST SUMMARY")
        print(f"frames={frames} elapsed={elapsed:.1f}s fps={fps:.1f}")
        print(f"background_detection_frames={background_hits}")
        print(f"motion_detection_frames={motion_hits}")
        print(f"raw_warning_frames={raw_warning_hits}")
        print(f"warning_frames={warning_hits}")
        print(f"raw_warning_changes={raw_warning_changes}")
        print(f"warning_changes={warning_changes}")
        print(f"risk_levels={_format_counter(risk_counts)}")
        yolo_stats = yolo_vision.get_stats()
        print(f"yolo_requested_by_config={yolo_stats['config_enabled']}")
        print(f"yolo_active={yolo_stats['enabled']}")
        print(f"yolo_config_file={yolo_stats['config_path']}")
        print(f"yolo_python_executable={yolo_stats['python_executable']}")
        print(f"yolo_model_path={yolo_stats['model_path']}")
        print(f"yolo_confidence={yolo_stats['confidence']}")
        print(f"yolo_process_interval={yolo_stats['process_interval']}")
        print(f"yolo_allowlist={yolo_stats['allowlist']}")
        print(f"yolo_detection_frames={yolo_hits}")
        print(f"yolo_final_frames={yolo_final_hits}")
        print(f"yolo_inference_runs={yolo_stats['inference_runs']}")
        print(f"yolo_labels={_format_counter(yolo_label_counts)}")
        print(f"yolo_avg_inference={_format_ms(yolo_stats['average_inference_ms'])}")
        print(f"yolo_last_error={yolo_stats['last_error'] or 'none'}")
        print(f"audio_output_active={audio_output_active} ({audio_source})")
        print(f"beep_candidate_frames={beep_candidate_frames}")
        print(f"beep_candidate_patterns={_format_counter(beep_pattern_counts)}")

        _append_test_log(
            {
                "elapsed": elapsed,
                "camera_index": camera.camera_index,
                "camera_width": actual_width,
                "camera_height": actual_height,
                "processing_width": processing_width,
                "processing_height": processing_height,
                "camera_fps": actual_fps,
                "audio_output_active": audio_output_active,
                "audio_source": audio_source,
                "beep_candidate_frames": beep_candidate_frames,
                "beep_pattern_counts": beep_pattern_counts,
                "background_settle_seconds": background_wait_seconds,
                "background_capture_frames": BACKGROUND_CAPTURE_FRAMES,
                "frames": frames,
                "fps": fps,
                "background_hits": background_hits,
                "motion_hits": motion_hits,
                "raw_warning_hits": raw_warning_hits,
                "warning_frames": warning_hits,
                "raw_warning_changes": raw_warning_changes,
                "warning_changes": warning_changes,
                "mode_counts": mode_counts,
                "source_counts": source_counts,
                "region_counts": region_counts,
                "closeness_counts": closeness_counts,
                "risk_counts": risk_counts,
                "distance_seen": distance_seen,
                "yolo_hits": yolo_hits,
                "yolo_final_hits": yolo_final_hits,
                "yolo_label_counts": yolo_label_counts,
                "yolo_stats": yolo_stats,
            }
        )
        print(f"LIVE TEST: log appended to {TEST_LOG_PATH}")

    finally:
        set_audio_override(None)
        camera.stop()
        if show_window:
            cv2.destroyAllWindows()


def _parse_args():
    parser = argparse.ArgumentParser(description="Run a live Visual Guide camera test.")
    parser.add_argument(
        "--camera-index",
        type=int,
        default=None,
        help="Camera index to test. Leave empty to use config.py default.",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=TEST_SECONDS,
        help="How long to run after background capture.",
    )
    parser.add_argument(
        "--background-seconds",
        type=float,
        default=BACKGROUND_WAIT_SECONDS,
        help="How long to wait with an empty view before capturing background.",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Run without showing the OpenCV camera window.",
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Temporarily enable beep audio output for this test run.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    run_test(
        camera_index=args.camera_index,
        test_seconds=args.seconds,
        background_wait_seconds=args.background_seconds,
        show_window=not args.no_window,
        audio_enabled=args.audio,
    )
