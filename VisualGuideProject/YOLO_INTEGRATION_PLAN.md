# YOLO Integration Plan

Date: 2026-07-12

## Why add YOLO

The current OpenCV detectors are fast, but they only know that pixels changed or
moved. YOLO can add semantic object labels such as:

- `person`
- `bicycle`
- `car`
- `chair`
- `backpack`

This helps the guide decide whether a detected moving/changing object is likely
to matter for a walking user.

## How YOLO should help this project

YOLO should not replace the fast OpenCV detectors yet.

Instead, the intended fusion is:

```text
background detection
+ frame-to-frame motion detection
+ YOLO label/confidence detection
+ approach-risk grading
-> final warning decision
```

Examples:

- A `person` moving into the center path should be higher priority.
- A `bicycle` or `car` crossing ahead should be high priority.
- A random background texture should not become high risk only because pixels
  changed.

## Current code state

YOLO is now enabled for controlled laptop testing:

```python
YOLO_ENABLED = True
YOLO_PROCESS_INTERVAL = 10
YOLO_IMAGE_SIZE = 320
```

Current code preparation/testing:

- Base `ultralytics` package installed in `.venv-win`.
- `requirements-yolo.txt` installs base `ultralytics` first. The heavier
  `[export]` extra is saved for later Raspberry Pi/NCNN export work.
- `yolo26n.pt` downloaded and loaded successfully.
- Ultralytics settings and Matplotlib cache are redirected to project-local
  folders so tests do not require AppData write access.
- `config.py` now uses `YOLO_MODEL_PATH = "yolo26n.pt"` as the first target.
- `yolo_vision_api.py` now supports:
  - class allowlist
  - class danger weights
  - model/inference timing stats
  - cached detections between slow YOLO frames
  - choosing the most safety-relevant YOLO box instead of only the largest box
- `detection_api.py` can use YOLO `danger_weight` / `priority_score` as a
  tie-breaker.
- `LIVE_CAMERA_TEST.py` now logs YOLO metrics.

## First laptop test result

Completed on 2026-07-12:

- Camera index `1`: unavailable during this run.
- Camera index `0`: completed no-window test.
- Approx FPS: `26.8`
- YOLO average inference: `84.2 ms`
- YOLO inference cadence: every `10` frames.
- YOLO produced the selected final detection on most frames.

Interpretation:

- Current laptop performance is acceptable enough for more testing.
- YOLO is now the dominant detector when it sees a clear object/person, so the
  next design decision is whether static YOLO objects should warn immediately
  or whether YOLO should mostly boost/classify motion/background/risk evidence.

## Current fusion decision

YOLO should currently work as object recognition, not as the main danger
detector.

Current first-recognition classes:

- `person`
- `chair`
- `car`
- `bicycle`

Current warning authority:

- background-difference detection
- frame-to-frame motion detection
- 9-region position
- rough distance grade
- approach-risk trend

Fusion rule:

- If background/motion finds a warning candidate and YOLO sees the same target,
  YOLO adds the object label and confidence.
- If YOLO sees a class by itself but background/motion/risk does not support it,
  YOLO does not create a warning.

This means the project can say `person ahead` or `car on right` when the danger
logic agrees, while avoiding warnings from static YOLO-only detections.

## Recommended next laptop test

Run a visible test after the intended USB camera is available:

```powershell
.\.venv-win\Scripts\python.exe LIVE_CAMERA_TEST.py --camera-index 1 --seconds 15 --background-seconds 3
```

If camera index `1` is unavailable, use index `0`:

```powershell
.\.venv-win\Scripts\python.exe LIVE_CAMERA_TEST.py --camera-index 0 --seconds 15 --background-seconds 3
```

## Raspberry Pi 4B plan

The Raspberry Pi 4B is likely too slow for full PyTorch YOLO every frame.

Recommended Pi path:

1. Start with the nano model only.
2. Export to NCNN on the Pi or compatible ARM environment.
3. Use the exported NCNN model path as `YOLO_MODEL_PATH`.
4. Keep `YOLO_PROCESS_INTERVAL` around `10` to `15`.
5. Keep OpenCV background/motion detection running fast every frame.

## What to measure

The live test now records:

- YOLO enabled/disabled
- YOLO detection frames
- YOLO final frames
- YOLO inference runs
- YOLO inference hits
- YOLO cached returns
- YOLO average inference time
- YOLO last inference time

Decision target:

- If FPS drops too much, increase `YOLO_PROCESS_INTERVAL`.
- If YOLO is useful but too slow on Pi, export to NCNN.
- If YOLO labels are noisy, add a class allowlist.
