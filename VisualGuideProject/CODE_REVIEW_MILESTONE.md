# Visual Guide Code Review Milestone

Date: 2026-07-11

## Main decision

We simplified the robot behavior from two explicit modes:

- `standby`
- `moving`

to one continuous mode:

- `guide`

Reason: the camera should keep detecting possible obstacles whether the robot is
moving or not. The old mode switch added extra state, extra warning messages,
and a different detection path for each mode. That made the project harder to
tune and left less clean space for YOLO.

## Code changed in this milestone

### `detection_api.py`

- New shared detection pipeline.
- Runs background, frame-to-frame motion, and YOLO candidates in one continuous
  loop.
- Holds shared helpers:
  - `has_detection()`
  - `choose_primary_detection()`
  - `combine_detections()`
  - `make_display_detection()`
  - `ContinuousDetectionPipeline`

### `main.py`

- Rewritten around the continuous `guide` loop.
- No longer imports or uses `ModeManager`.
- Motion score is still calculated, but only as a debug signal.
- Startup still captures a stable background.
- Each frame now follows the same path:
  1. read camera frame
  2. estimate motion score for debug
  3. run continuous detection pipeline
  4. stabilize final detection
  5. estimate region, closeness, distance
  6. output warning and draw debug window

### `LIVE_CAMERA_TEST.py`

- Updated to use the same `ContinuousDetectionPipeline` as the real app.
- This keeps tests aligned with robot behavior.
- YOLO is now part of the test path, but it remains inactive while
  `YOLO_ENABLED = False`.

### `config.py`

- Added `GUIDE_MODE = "guide"`.
- The old standby/moving settings were later removed after guide-mode testing.

## Legacy cleanup completed

On 2026-07-12, after guide-mode testing, the rollback mode code was removed:

- deleted `mode_manager.py`
- removed old standby/moving config values
- removed old helper functions:
  - `guidance_api.draw_detection()`
  - `vision_api.detect_obstacle()`

## Code audit notes

### Looks good / keep

- `camera_api.py`: clear camera wrapper; useful Windows/Linux backend handling.
- `background_api.py`: clean stable background capture helper.
- `distance_api.py`: simple and isolated; needs calibration, not structural
  cleanup.
- `stability_api.py`: useful but slightly advanced; keep isolated.
- `yolo_vision_api.py`: already isolated, which is good for enabling YOLO later.

### Good, but can be cleaned later

- `vision_api.py`: contains both background detection and frame-to-frame motion
  detection. This is okay now. If it grows more, split into
  `background_vision_api.py` and `motion_vision_api.py`.
- `guidance_api.py`: now keeps the active multi-box `draw_detections()` helper.
- `output_api.py`: speech and beep are in one file. This is okay while audio is
  disabled, but if audio work grows, split beep/speech output into smaller
  modules.
- `LIVE_CAMERA_TEST.py`: intentionally long because it handles camera preview,
  metrics, logging, and CLI arguments. Later it can be split into test runner,
  overlay, and log writer sections.

## Recommended next cleanup order

1. Continue tuning warning sensitivity from controlled camera tests.
2. Add YOLO test mode only after the continuous pipeline is stable.
3. Calibrate distance with a known object and known distances.
4. Split `LIVE_CAMERA_TEST.py` only if test logging/overlay code becomes hard
   to maintain.
