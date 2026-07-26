# Visual Guide Simplification Review

Date: 2026-07-11

## Short conclusion

The project is not messy because the core logic is bad. It looks busy because
we have been keeping experiment history, test logs, and rollback code while
improving the prototype.

Recommended strategy:

1. Do not combine the main robot logic into one large file.
2. Keep the completed legacy cleanup.
3. Avoid reintroducing unused compatibility helpers.
4. Keep camera, detection, risk, warning, and output separated.
5. Split the large live test only if it becomes hard to maintain.

## Current active robot flow

```text
main.py
  -> CameraAPI reads fresh frame
  -> VisionAPI detects background changes and frame-to-frame motion
  -> YOLOVisionAPI optionally detects semantic objects
  -> ContinuousDetectionPipeline chooses final object
  -> DetectionStabilizer smooths box and warning
  -> ApproachRiskTracker grades whether object is approaching
  -> guidance/distance APIs describe position and rough distance
  -> warning_api creates warning text
  -> output_api prints/beeps/speaks
```

This flow is good. It is understandable and leaves space for YOLO.

## Python file review

| File | Current role | Recommendation |
|---|---|---|
| `main.py` | Real app entry point and orchestration | Keep. It is now much cleaner after continuous guide simplification. |
| `config.py` | User control panel and tuning values | Keep. Legacy mode settings have been removed. |
| `camera_api.py` | Camera open/read/resize/low-latency handling | Keep separate. Hardware code should stay isolated. |
| `background_api.py` | Stable multi-frame background capture | Keep separate for now. It coordinates camera + vision + preview callback. |
| `vision_api.py` | Background difference and frame-to-frame motion detection | Keep. Later maybe split only if optical flow is added and file grows too much. |
| `detection_api.py` | Shared continuous detection pipeline and detection selection | Keep. This is the right place for detector fusion. |
| `risk_api.py` | Approach-risk grading over time | Keep. It is complex enough to deserve its own file. |
| `stability_api.py` | Box smoothing, warning hysteresis, background persistence | Keep. Could later move `DetectionPersistenceFilter` into `detection_api.py`, but not urgent. |
| `guidance_api.py` | 9-region grid, direction, closeness, drawing | Keep. Old single-box drawing helper has been removed. |
| `distance_api.py` | Approximate monocular distance | Keep separate because calibration/hardware distance may grow later. |
| `warning_api.py` | Converts detection state into warning text | Keep separate from output. |
| `output_api.py` | Print/beep/speech output and anti-spam | Keep separate. This protects camera speed from audio behavior. |
| `yolo_vision_api.py` | Optional YOLO wrapper | Keep separate. YOLO will need special installation/performance handling. |
| `motion_api.py` | Global motion score for debug overlay | Optional. Keep for now; later combine into `detection_api.py` or remove if unused. |
| `LIVE_CAMERA_TEST.py` | Real camera test runner, overlay, metrics, log writer | Keep for now. It is long, but it is test-only. Split later only if it becomes painful. |

## Best things to simplify first

### 1. Legacy mode-switch code

Status: completed on 2026-07-12.

Removed:

- `mode_manager.py`
- `MOTION_THRESHOLD`
- `MODE_SWITCH_SECONDS`
- `MODE_MOVING`
- `MODE_STANDBY`
- `MOVING_FALLBACK_TO_BACKGROUND`

Why:

- The active app did not use them.
- They made `config.py` look more complicated than the actual robot behavior.

### 2. Unused old helpers

Status: completed on 2026-07-12.

Removed:

- `guidance_api.draw_detection()`
- `vision_api.detect_obstacle()`

Why:

- The active app uses `draw_detections()`.
- The active app uses `detect_obstacles()` and the continuous pipeline.
- These old helpers are compatibility leftovers.

### 3. Decide what to do with `motion_api.py`

Current situation:

- `motion_api.py` only provides a global motion score.
- That score is now debug information, not mode switching.

Options:

- Keep it if you like seeing `Motion: 0.xxx` in the overlay.
- Move the class into `detection_api.py` if you want one fewer file.
- Remove it if the overlay no longer needs global motion.

My recommendation:

- Keep it until the next live test. It is tiny and harmless.

## Things I would not combine yet

### Do not combine `warning_api.py` and `output_api.py`

Reason:

- Warning text generation is logic.
- Beep/speech/printing is side effect.
- Keeping them separate helps prevent audio from slowing the camera loop again.

### Do not combine `risk_api.py` into `main.py`

Reason:

- Approach risk is a real algorithm now.
- If it stays isolated, we can tune/test it without turning `main.py` into a
  giant file.

### Do not combine `yolo_vision_api.py` with the normal OpenCV vision code

Reason:

- YOLO has different dependencies, model files, and Raspberry Pi performance
  concerns.
- Keeping it isolated makes it easy to disable or replace.

### Do not split `vision_api.py` yet

Reason:

- It currently has two related OpenCV detectors:
  - background difference
  - frame-to-frame motion
- Splitting now would add files without much benefit.

Split only when we add background optical flow or feature tracking.

## Documentation review

| File | Role | Recommendation |
|---|---|---|
| `PROJECT_OPTIMIZATION_PLAN.md` | Current roadmap | Keep. This is the active plan. |
| `TEST_LOG.md` | Lab notebook for real tests | Keep append-only. |
| `CHANGELOG_CODE_OPTIMIZATION.md` | Historical code-change record | Keep append-only. |
| `APPROACH_RISK_DESIGN.md` | Detailed explanation of approach-risk idea | Keep. Useful for your design report. |
| `CODE_REVIEW_MILESTONE.md` | Previous milestone note | Keep for now, but it can later be replaced by this review. |
| `SIMPLIFICATION_REVIEW.md` | Current simplification decision guide | Keep as the current cleanup map. |

## Folder hygiene

Current generated folders:

- `.venv-win/`
- `venv/`
- `__pycache__/`

They are already in `.gitignore`.

Recommendation:

- Keep `.venv-win/` because it is the environment we have been using.
- Do not delete `venv/` until we confirm it is not needed by your local setup.
- `__pycache__/` can be deleted safely later, but it will come back whenever
  Python runs.

## Suggested cleanup stages

### Stage A: no-risk cleanup after guide-mode tests

Status: completed.

### Stage B: readability cleanup

- Consider moving test logging helpers from `LIVE_CAMERA_TEST.py` into
  `test_log_api.py`.
- Consider moving test overlay helpers from `LIVE_CAMERA_TEST.py` into
  `test_overlay_api.py`.

Only do this if live testing code becomes annoying to edit.

### Stage C: advanced perception cleanup

- Add background optical-flow compensation as a separate module, likely
  `background_flow_api.py`.
- Keep it separate until Raspberry Pi performance is known.

### Stage D: YOLO stage

- Enable YOLO in the existing `yolo_vision_api.py` wrapper.
- Do not spread YOLO code into `main.py`.
- Add a YOLO-specific test mode if needed.

## Current immediate decision

The first cleanup stage is complete:

1. `mode_manager.py` was deleted.
2. Legacy mode settings were removed from `config.py`.
3. Old helper functions were removed.

The next cleanup should wait until testing shows a real pain point. The most
likely next candidate is splitting `LIVE_CAMERA_TEST.py` into smaller test
logging and overlay helpers, but only if it becomes annoying to edit.
