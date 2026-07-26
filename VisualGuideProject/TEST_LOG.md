# Visual Guide Test Log

This file records each real camera test, what we noticed, and what should be
optimized next.

## 2026-07-11 - First live camera test

- Duration: 25.1s
- Frames: 251
- Approx FPS: 10.0 while printing detailed diagnostics
- Background detection frames: 80
- Motion detection frames: 208
- Warning frames: 197
- Camera: 320 x 240 at 30 FPS

What we noticed:
- Frame-to-frame motion detection worked well and was more responsive than
  background detection alone.
- Regions such as `bottom_center`, `bottom_left`, and `bottom_right` appeared.
- Approximate distance values appeared, including around `0.7 m` to `1.9 m`.
- Warning text sometimes changed quickly between caution/stop and left/center/right.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Calibrate distance estimation before using distance in spoken/beep warnings.
- Keep motion detection active in moving mode.

## 2026-07-11 - Display box simplification

What we noticed:
- The camera window showed green background boxes and orange motion boxes at
  the same time.
- That was useful for debugging detector sources, but confusing for normal
  testing because it looked like two competing trackers.

Need to optimize:
- Show one final decision box by default.
- Keep a config switch for all raw detector boxes when debugging.

Change:
- Added `SHOW_ALL_DETECTION_SOURCES = False`.
- Final decision boxes now draw as yellow with a `FINAL source` label.

## 2026-07-11 - New camera index 1 test

What we noticed:
- Camera index `1` opened successfully, so it is likely the newly attached
  camera.
- The camera reported `640 x 480` even though the project requested `320 x 240`.
- Motion detection was very active, but warning changes were high.
- Because the new camera produced larger frames, the existing sensitivity
  settings became too aggressive.

Need to optimize:
- Force all captured frames back to the configured processing size.
- Retest camera index `1` after resizing to confirm speed and sensitivity.

Change:
- `CameraAPI.get_frame()` now resizes frames to `FRAME_WIDTH x FRAME_HEIGHT`
  if the actual camera frame is larger or different.
- Windows camera capture now prefers DirectShow and retries short read failures.

## 2026-07-11 - Stabilizer implementation note

What we noticed:
- Camera index `1` was not visible when rescanned for the stabilizer test.
- Camera index `0` was available and used for a short no-window stabilizer test.
- Raw warning changes were `12`; stabilized warning changes were `3`.

Need to optimize:
- Reconnect or release the USB camera, then rerun with `--camera-index 1`.
- Tune stabilizer settings on the actual target camera after it is visible again.

Change:
- Added `stability_api.py`.
- `main.py` and `LIVE_CAMERA_TEST.py` now stabilize the final detection and
  warning text.
- `LIVE_CAMERA_TEST.py` now reports raw warning changes and stabilized warning
  changes separately.

## 2026-07-11 - Robust background capture implementation

What we noticed:
- Camera index `1` fired too many background detections after capture.
- A single background frame is fragile when camera exposure, lighting, or noise
  changes right after startup.

Need to optimize:
- Test whether median background capture reduces false background boxes.
- Tune settle time and frame count if camera index `1` still drifts.

Change:
- Added `background_api.py`.
- Added multi-frame median background capture to `VisionAPI`.
- The app and live test now use stable background capture instead of one-frame
  background capture.

## 2026-07-11 18:18:42 - Live camera test

- Duration: 25.1s
- Frames: 251
- Approx FPS: 10.0
- Background detection frames: 26
- Motion detection frames: 242
- Warning frames: 155
- Warning changes: 67
- Modes: standby: 251
- Sources: motion: 209, background: 37, none: 5
- Regions: middle_right: 59, bottom_right: 57, bottom_center: 57, middle_center: 54, bottom_left: 9
- Closeness: medium: 123, far: 91, close: 32, none: 5

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- Warning text changed often during the run.
- Diagnostic display and printing reduce test FPS; real app speed may be higher.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Stabilize direction/closeness before changing spoken or beep output.
- Calibrate distance with a known object at known distances.

## 2026-07-11 18:30:22 - Live camera test

- Duration: 25.0s
- Camera index: 1
- Camera size: 640 x 480
- Camera FPS reported: 30.0
- Frames: 236
- Approx FPS: 9.4
- Background detection frames: 101
- Motion detection frames: 232
- Warning frames: 126
- Warning changes: 100
- Modes: standby: 131, moving: 105
- Sources: motion: 213, background: 22, none: 1
- Regions: top_center: 48, bottom_center: 39, middle_center: 32, bottom_left: 30, bottom_right: 29
- Closeness: far: 109, medium: 83, close: 43, none: 1

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warning text changed often during the run.
- Diagnostic display and printing reduce test FPS; real app speed may be higher.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Stabilize direction/closeness before changing spoken or beep output.
- Calibrate distance with a known object at known distances.

## 2026-07-11 18:32:40 - Live camera test

- Duration: 15.0s
- Camera index: 1
- Camera reported size: 640 x 480
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Frames: 333
- Approx FPS: 22.2
- Background detection frames: 0
- Motion detection frames: 318
- Warning frames: 180
- Warning changes: 122
- Modes: standby: 333
- Sources: motion: 318, none: 15
- Regions: middle_center: 56, middle_left: 52, top_center: 47, bottom_left: 46, bottom_center: 43
- Closeness: far: 138, medium: 123, close: 57, none: 15

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warning text changed often during the run.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Stabilize direction/closeness before changing spoken or beep output.
- Calibrate distance with a known object at known distances.

## 2026-07-11 18:38:12 - Live camera test

- Duration: 10.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Frames: 302
- Approx FPS: 30.1
- Background detection frames: 56
- Motion detection frames: 21
- Raw warning frames: 44
- Warning frames: 46
- Raw warning changes: 12
- Warning changes: 3
- Modes: standby: 302
- Sources: none: 169, background: 130, motion: 3
- Regions: clear: 169, bottom_right: 111, bottom_left: 9, bottom_center: 9, middle_center: 4
- Closeness: none: 169, far: 89, medium: 30, close: 14

What we noticed:
- The stabilizer reduced warning changes compared with raw detection.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Calibrate distance with a known object at known distances.

## 2026-07-11 18:40:20 - Live camera test

- Duration: 15.0s
- Camera index: 1
- Camera reported size: 640 x 480
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Frames: 340
- Approx FPS: 22.7
- Background detection frames: 170
- Motion detection frames: 197
- Raw warning frames: 339
- Warning frames: 337
- Raw warning changes: 11
- Warning changes: 8
- Modes: standby: 340
- Sources: background: 335, motion: 4, none: 1
- Regions: bottom_right: 178, middle_left: 102, bottom_center: 59, clear: 1
- Closeness: close: 333, medium: 6, none: 1

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Calibrate distance with a known object at known distances.

## 2026-07-12 - Legacy cleanup note

Change:
- Deleted old standby/walking `mode_manager.py`.
- Removed legacy mode-switch values from `config.py`.
- Removed unused old helpers:
  - `guidance_api.draw_detection()`
  - `vision_api.detect_obstacle()`

Validation:
- No remaining Python references to the removed names.
- All Python files compile.
- Main app and live test imports pass.

## 2026-07-12 - YOLO preparation note

Change:
- Added optional `requirements-yolo.txt`.
- Updated `yolo_vision_api.py` for class weighting, optional class filtering,
  caching, and inference timing stats.
- Updated live test logging with YOLO metrics.
- Added `YOLO_INTEGRATION_PLAN.md`.

Current status:
- `YOLO_ENABLED` is still `False`.
- No YOLO dependency installation has been run yet.

Next test:
- Install optional YOLO dependencies when ready.
- Enable YOLO for a short no-window metric test before trying a visible-window
  test.

## 2026-07-11 18:45:33 - Live camera test

- Duration: 8.0s
- Camera index: 1
- Camera reported size: 640 x 480
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 182
- Approx FPS: 22.7
- Background detection frames: 79
- Motion detection frames: 15
- Raw warning frames: 78
- Warning frames: 78
- Raw warning changes: 9
- Warning changes: 3
- Modes: standby: 182
- Sources: background: 159, none: 19, motion: 4
- Regions: middle_left: 74, middle_center: 58, top_left: 24, clear: 19, bottom_left: 5
- Closeness: far: 85, medium: 54, close: 24, none: 19

What we noticed:
- The stabilizer reduced warning changes compared with raw detection.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Calibrate distance with a known object at known distances.

## 2026-07-11 18:46:54 - Live camera test

- Duration: 8.0s
- Camera index: 1
- Camera reported size: 640 x 480
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 182
- Approx FPS: 22.7
- Background detection frames: 73
- Motion detection frames: 1
- Raw warning frames: 32
- Warning frames: 38
- Raw warning changes: 3
- Warning changes: 3
- Modes: standby: 182
- Sources: background: 145, none: 37
- Regions: top_center: 75, middle_left: 63, clear: 37, middle_center: 5, top_left: 2
- Closeness: far: 113, none: 37, medium: 32

What we noticed:
- The background persistence filter reduced warning spam: compared with the
  previous 8-second index `1` run, raw warning frames dropped from 78 to 32.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Tune `BACKGROUND_DETECTION_STABLE_FRAMES`; current value is 2 processed
  background cycles.
- Calibrate distance with a known object at known distances.

## 2026-07-11 - Approach-risk grading implementation

What we noticed:
- Exact distance is not reliable enough to be the only danger signal.
- 9-region motion and box-size growth can tell us whether an object is moving
  into the user's path.

Change:
- Added `risk_api.py`.
- Added approach-risk grading to `main.py`, `warning_api.py`, and
  `LIVE_CAMERA_TEST.py`.
- Live tests now print/log risk levels.

Need to optimize:
- Run a real camera test with a face/object moving left-to-center, right-to-
  center, top-to-bottom, and side-to-side without size growth.
- Tune approach-risk thresholds after that test.

## 2026-07-11 19:22:47 - Live camera test

- Duration: 20.0s
- Camera index: 1
- Camera reported size: 640 x 480
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 450
- Approx FPS: 22.5
- Background detection frames: 8
- Motion detection frames: 415
- Raw warning frames: 269
- Warning frames: 353
- Raw warning changes: 171
- Warning changes: 21
- Modes: guide: 450
- Sources: motion: 445, background: 4, none: 1
- Regions: bottom_right: 97, bottom_center: 65, top_center: 56, bottom_left: 52, middle_center: 45
- Closeness: far: 222, medium: 164, close: 63, none: 1
- Risk levels: none: 257, low: 93, medium: 62, high: 38

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-11 - Post guide-mode tuning

What we noticed:
- The continuous `guide` loop stayed fast at about `22.5 FPS`.
- Motion detection was too active: `415 / 450` frames.
- Stabilization helped, but warnings still changed more than desired.

Change:
- Raised motion-object thresholds.
- Made approach-risk grading stricter.
- Reduced stale detection/warning hold time.
- Made non-urgent warning text changes require slightly stronger persistence.

Need to optimize:
- Run another camera index `1` test and compare against the `19:22:47` run.
- Target fewer motion detections, fewer warning frames, and fewer warning
  changes while still catching real approaching objects.

## 2026-07-11 19:27:09 - Live camera test

- Duration: 20.1s
- Camera index: 1
- Camera reported size: 640 x 480
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 20
- Approx FPS: 1.0
- Background detection frames: 9
- Motion detection frames: 0
- Raw warning frames: 0
- Warning frames: 0
- Raw warning changes: 0
- Warning changes: 0
- Modes: guide: 20
- Sources: background: 17, none: 3
- Regions: top_left: 17, clear: 3
- Closeness: far: 17, none: 3
- Risk levels: none: 20

What we noticed:
- Diagnostic display and printing reduce test FPS; real app speed may be higher.
- Follow-up no-window diagnostic at `19:27:33` reached `22.8 FPS`, so this
  `1.0 FPS` visible-window run should be treated as an invalid GUI/camera
  hiccup, not as algorithm slowdown.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- If visible-window testing repeats at about `1 FPS`, restart/replug the camera
  or use `--no-window` for metric comparison.
- Calibrate distance with a known object at known distances.

## 2026-07-11 19:27:33 - Live camera test

- Duration: 5.0s
- Camera index: 1
- Camera reported size: 640 x 480
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 2.0
- Background capture frames: 12
- Frames: 114
- Approx FPS: 22.8
- Background detection frames: 35
- Motion detection frames: 56
- Raw warning frames: 80
- Warning frames: 69
- Raw warning changes: 30
- Warning changes: 3
- Modes: guide: 114
- Sources: background: 69, motion: 37, none: 8
- Regions: middle_center: 35, middle_right: 26, bottom_center: 13, top_center: 10, clear: 8
- Closeness: close: 47, medium: 30, far: 29, none: 8
- Risk levels: none: 53, medium: 32, low: 20, high: 9

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Calibrate distance with a known object at known distances.

## 2026-07-11 19:32:49 - Live camera test

- Duration: 25.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 750
- Approx FPS: 30.0
- Background detection frames: 196
- Motion detection frames: 425
- Raw warning frames: 400
- Warning frames: 361
- Raw warning changes: 71
- Warning changes: 20
- Modes: guide: 750
- Sources: background: 368, motion: 285, none: 97
- Regions: middle_center: 308, clear: 97, bottom_center: 80, top_center: 77, middle_right: 63
- Closeness: far: 269, close: 195, medium: 189, none: 97
- Risk levels: none: 464, low: 177, medium: 80, high: 29

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-11 19:33:46 - Live camera test

- Duration: 25.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 752
- Approx FPS: 30.0
- Background detection frames: 231
- Motion detection frames: 288
- Raw warning frames: 542
- Warning frames: 496
- Raw warning changes: 65
- Warning changes: 20
- Modes: guide: 752
- Sources: background: 463, motion: 221, none: 68
- Regions: middle_right: 396, middle_center: 102, clear: 68, bottom_center: 58, bottom_right: 41
- Closeness: medium: 311, close: 209, far: 164, none: 68
- Risk levels: none: 541, low: 131, medium: 63, high: 17

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-11 19:37:22 - Live camera test

- Duration: 100.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 3002
- Approx FPS: 30.0
- Background detection frames: 331
- Motion detection frames: 1695
- Raw warning frames: 1229
- Warning frames: 1024
- Raw warning changes: 416
- Warning changes: 52
- Modes: guide: 3002
- Sources: motion: 1769, none: 762, background: 471
- Regions: clear: 762, middle_right: 533, bottom_right: 336, middle_center: 328, bottom_center: 280
- Closeness: far: 1104, none: 762, medium: 748, close: 388
- Risk levels: none: 2100, low: 650, medium: 189, high: 63

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-11 20:04:03 - Live camera test

- Duration: 70.2s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 2108
- Approx FPS: 30.0
- Background detection frames: 626
- Motion detection frames: 732
- Raw warning frames: 881
- Warning frames: 762
- Raw warning changes: 138
- Warning changes: 45
- Modes: guide: 2108
- Sources: background: 1181, motion: 523, none: 404
- Regions: clear: 404, bottom_left: 374, middle_right: 278, bottom_center: 262, middle_center: 243
- Closeness: far: 881, medium: 413, close: 410, none: 404
- Risk levels: none: 1503, low: 406, medium: 161, high: 38

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 15:52:23 - Live camera test

- Duration: 12.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 3.0
- Background capture frames: 12
- Frames: 322
- Approx FPS: 26.8
- Background detection frames: 102
- Motion detection frames: 32
- Raw warning frames: 313
- Warning frames: 313
- Raw warning changes: 4
- Warning changes: 4
- Modes: guide: 322
- Sources: yolo: 312, none: 9, motion: 1
- Regions: middle_center: 243, middle_left: 50, bottom_center: 20, clear: 9
- Closeness: close: 313, none: 9
- Risk levels: none: 313, high: 7, low: 2
- YOLO enabled: True
- YOLO detection frames: 313
- YOLO final frames: 312
- YOLO inference runs: 32
- YOLO inference hits: 32
- YOLO cached returns: 281
- YOLO avg inference: 84.2 ms
- YOLO last inference: 33.0 ms

What we noticed:
- Warnings appeared on most frames, so the detector is sensitive.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Calibrate distance with a known object at known distances.

## 2026-07-12 15:57:16 - Live camera test

- Duration: 20.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 3.0
- Background capture frames: 12
- Frames: 599
- Approx FPS: 29.9
- Background detection frames: 43
- Motion detection frames: 201
- Raw warning frames: 554
- Warning frames: 550
- Raw warning changes: 14
- Warning changes: 7
- Modes: guide: 599
- Sources: yolo: 588, background: 8, none: 3
- Regions: middle_center: 250, bottom_center: 148, bottom_right: 98, bottom_left: 60, middle_left: 30
- Closeness: close: 382, medium: 172, far: 42, none: 3
- Risk levels: none: 524, low: 40, medium: 30, high: 5
- YOLO enabled: True
- YOLO detection frames: 590
- YOLO final frames: 588
- YOLO inference runs: 59
- YOLO inference hits: 59
- YOLO cached returns: 531
- YOLO avg inference: 44.3 ms
- YOLO last inference: 46.4 ms

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Calibrate distance with a known object at known distances.

## 2026-07-12 16:04:22 - Live camera test

- Duration: 10.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 3.0
- Background capture frames: 12
- Frames: 285
- Approx FPS: 28.5
- Background detection frames: 0
- Motion detection frames: 0
- Raw warning frames: 0
- Warning frames: 0
- Raw warning changes: 0
- Warning changes: 0
- Modes: guide: 285
- Sources: none: 285
- Regions: clear: 285
- Closeness: none: 285
- Risk levels: none: 285
- YOLO enabled: True
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 28
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: 65.1 ms
- YOLO last inference: 63.0 ms

What we noticed:
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Review the camera window and decide the next tuning target.

## 2026-07-12 16:08:54 - Live camera test

- Duration: 25.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Background settle seconds: 3.0
- Background capture frames: 12
- Frames: 739
- Approx FPS: 29.5
- Background detection frames: 151
- Motion detection frames: 382
- Raw warning frames: 330
- Warning frames: 310
- Raw warning changes: 55
- Warning changes: 13
- Modes: guide: 739
- Sources: background: 264, none: 246, motion: 229
- Regions: clear: 246, bottom_center: 121, middle_right: 119, bottom_right: 53, top_center: 48
- Closeness: none: 246, close: 206, far: 177, medium: 110
- Risk levels: none: 522, low: 137, medium: 62, high: 18
- YOLO enabled: True
- YOLO detection frames: 660
- YOLO final frames: 0
- YOLO inference runs: 73
- YOLO inference hits: 66
- YOLO cached returns: 594
- YOLO labels: person: 380, chair: 280
- YOLO avg inference: 46.1 ms
- YOLO last inference: 55.0 ms

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 17:22:07 - Live camera test

- Duration: 25.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio test enabled: True
- Background settle seconds: 3.0
- Background capture frames: 12
- Frames: 740
- Approx FPS: 29.5
- Background detection frames: 218
- Motion detection frames: 491
- Raw warning frames: 467
- Warning frames: 424
- Raw warning changes: 80
- Warning changes: 37
- Modes: guide: 740
- Sources: background: 364, motion: 275, none: 101
- Regions: bottom_right: 267, middle_center: 199, clear: 101, bottom_center: 94, middle_right: 46
- Closeness: medium: 301, far: 175, close: 163, none: 101
- Risk levels: none: 462, low: 165, medium: 75, high: 38
- YOLO enabled: True
- YOLO detection frames: 561
- YOLO final frames: 0
- YOLO inference runs: 74
- YOLO inference hits: 57
- YOLO cached returns: 504
- YOLO labels: person: 561
- YOLO avg inference: 46.2 ms
- YOLO last inference: 35.9 ms

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio beep output was enabled only for this live test run.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 17:24:28 - Live camera test

- Duration: 25.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio test enabled: False
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 752
- Approx FPS: 30.1
- Background detection frames: 305
- Motion detection frames: 544
- Raw warning frames: 531
- Warning frames: 498
- Raw warning changes: 82
- Warning changes: 44
- Modes: guide: 752
- Sources: background: 541, motion: 189, none: 22
- Regions: bottom_left: 313, middle_center: 203, bottom_center: 92, middle_left: 82, middle_right: 27
- Closeness: close: 274, medium: 253, far: 203, none: 22
- Risk levels: none: 464, low: 151, medium: 104, high: 33
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was disabled for this run.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 17:24:59 - Live camera test

- Duration: 8.1s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio test enabled: False
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 244
- Approx FPS: 30.2
- Background detection frames: 101
- Motion detection frames: 188
- Raw warning frames: 169
- Warning frames: 152
- Raw warning changes: 25
- Warning changes: 13
- Modes: guide: 244
- Sources: background: 152, motion: 75, none: 17
- Regions: middle_center: 83, bottom_left: 80, bottom_center: 46, clear: 17, middle_right: 15
- Closeness: medium: 94, close: 74, far: 59, none: 17
- Risk levels: none: 144, low: 71, medium: 22, high: 7
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was disabled for this run.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 17:29:37 - Live camera test

- Duration: 11.2s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio test enabled: False
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 336
- Approx FPS: 30.1
- Background detection frames: 152
- Motion detection frames: 209
- Raw warning frames: 272
- Warning frames: 245
- Raw warning changes: 23
- Warning changes: 10
- Modes: guide: 336
- Sources: background: 293, motion: 38, none: 5
- Regions: bottom_center: 145, bottom_left: 134, middle_right: 35, middle_center: 10, top_center: 6
- Closeness: medium: 229, far: 60, close: 42, none: 5
- Risk levels: none: 274, low: 50, medium: 12
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was disabled for this run.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Calibrate distance with a known object at known distances.

## 2026-07-12 17:30:35 - Live camera test

- Duration: 18.3s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio test enabled: True
- Background settle seconds: 3.0
- Background capture frames: 12
- Frames: 535
- Approx FPS: 29.2
- Background detection frames: 187
- Motion detection frames: 403
- Raw warning frames: 409
- Warning frames: 351
- Raw warning changes: 105
- Warning changes: 37
- Modes: guide: 535
- Sources: background: 301, motion: 205, none: 29
- Regions: bottom_left: 174, bottom_center: 93, middle_center: 78, middle_right: 55, bottom_right: 45
- Closeness: medium: 226, close: 174, far: 106, none: 29
- Risk levels: none: 294, low: 128, medium: 93, high: 20
- YOLO enabled: True
- YOLO detection frames: 496
- YOLO final frames: 0
- YOLO inference runs: 53
- YOLO inference hits: 50
- YOLO cached returns: 446
- YOLO labels: person: 496
- YOLO avg inference: 48.0 ms
- YOLO last inference: 45.7 ms

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio beep output was enabled only for this live test run.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 18:31:12 - Live camera test

- Duration: 10.1s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio test enabled: False
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 304
- Approx FPS: 30.2
- Background detection frames: 73
- Motion detection frames: 33
- Raw warning frames: 110
- Warning frames: 88
- Raw warning changes: 5
- Warning changes: 5
- Modes: guide: 304
- Sources: none: 150, background: 144, motion: 10
- Regions: clear: 150, bottom_right: 116, bottom_center: 22, middle_right: 16
- Closeness: none: 150, close: 70, far: 44, medium: 40
- Risk levels: none: 239, low: 57, high: 7, medium: 1
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a

What we noticed:
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was disabled for this run.

Need to optimize:
- Calibrate distance with a known object at known distances.

## 2026-07-12 18:35:29 - Live camera test

- Duration: 25.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio test enabled: False
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 752
- Approx FPS: 30.0
- Background detection frames: 262
- Motion detection frames: 165
- Raw warning frames: 530
- Warning frames: 521
- Raw warning changes: 30
- Warning changes: 22
- Modes: guide: 752
- Sources: background: 539, none: 131, motion: 82
- Regions: bottom_right: 411, clear: 131, middle_center: 75, bottom_center: 59, middle_right: 45
- Closeness: close: 333, medium: 194, none: 131, far: 94
- Risk levels: none: 555, low: 146, medium: 29, high: 22
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a

What we noticed:
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- YOLO was disabled for this run.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 18:42:15 - Live camera test

- Duration: 25.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 91
- Beep candidate patterns: stop_ahead: 73, approach_ahead: 18
- Background settle seconds: 3.0
- Background capture frames: 12
- Frames: 677
- Approx FPS: 27.1
- Background detection frames: 254
- Motion detection frames: 384
- Raw warning frames: 601
- Warning frames: 559
- Raw warning changes: 67
- Warning changes: 23
- Modes: guide: 677
- Sources: background: 460, motion: 196, none: 21
- Regions: top_right: 221, middle_center: 162, bottom_center: 98, bottom_right: 92, middle_right: 67
- Closeness: medium: 446, close: 149, far: 61, none: 21
- Risk levels: none: 481, low: 121, medium: 61, high: 14
- YOLO enabled: True
- YOLO detection frames: 668
- YOLO final frames: 0
- YOLO inference runs: 67
- YOLO inference hits: 67
- YOLO cached returns: 601
- YOLO labels: person: 668
- YOLO avg inference: 81.1 ms
- YOLO last inference: 40.9 ms
- YOLO last error: none

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 18:43:29 - Live camera test

- Duration: 21.7s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 74
- Beep candidate patterns: stop_ahead: 45, approach_ahead: 29
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 653
- Approx FPS: 30.1
- Background detection frames: 125
- Motion detection frames: 402
- Raw warning frames: 353
- Warning frames: 321
- Raw warning changes: 59
- Warning changes: 20
- Modes: guide: 653
- Sources: motion: 267, background: 222, none: 164
- Regions: clear: 164, middle_right: 119, middle_center: 82, middle_left: 79, bottom_center: 55
- Closeness: medium: 211, none: 164, far: 153, close: 125
- Risk levels: none: 404, low: 149, medium: 82, high: 18
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a
- YOLO last error: No module named 'ultralytics'

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was disabled for this run.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 19:53:56 - Live camera test

- Duration: 52.1s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 124
- Beep candidate patterns: approach_ahead: 75, stop_ahead: 49
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 1562
- Approx FPS: 30.0
- Background detection frames: 46
- Motion detection frames: 1091
- Raw warning frames: 701
- Warning frames: 474
- Raw warning changes: 313
- Warning changes: 39
- Modes: guide: 1562
- Sources: motion: 1200, none: 298, background: 64
- Regions: clear: 298, bottom_center: 292, middle_left: 209, bottom_right: 174, middle_center: 160
- Closeness: far: 636, medium: 455, none: 298, close: 173
- Risk levels: none: 993, low: 363, medium: 153, high: 53
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a
- YOLO last error: No module named 'ultralytics'

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was disabled for this run.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 19:56:10 - Live camera test

- Duration: 63.8s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 285
- Beep candidate patterns: stop_ahead: 180, approach_ahead: 105
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 1916
- Approx FPS: 30.0
- Background detection frames: 136
- Motion detection frames: 1426
- Raw warning frames: 941
- Warning frames: 729
- Raw warning changes: 400
- Warning changes: 59
- Modes: guide: 1916
- Sources: motion: 1523, none: 234, background: 159
- Regions: middle_center: 438, middle_left: 264, clear: 234, bottom_center: 211, middle_right: 194
- Closeness: far: 837, medium: 607, close: 238, none: 234
- Risk levels: none: 1137, low: 468, medium: 265, high: 46
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a
- YOLO last error: No module named 'ultralytics'

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was disabled for this run.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 19:56:27 - Live camera test

- Duration: 1.6s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 0
- Beep candidate patterns: none
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 49
- Approx FPS: 30.9
- Background detection frames: 4
- Motion detection frames: 40
- Raw warning frames: 23
- Warning frames: 9
- Raw warning changes: 7
- Warning changes: 1
- Modes: guide: 49
- Sources: motion: 45, none: 2, background: 2
- Regions: middle_left: 17, bottom_left: 17, middle_right: 6, middle_center: 3, bottom_center: 3
- Closeness: far: 36, medium: 11, none: 2
- Risk levels: none: 18, medium: 18, low: 12, high: 1
- YOLO enabled: False
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a
- YOLO last error: No module named 'ultralytics'

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- No stable warning matched the beep policy, so no beep was expected.
- YOLO was disabled for this run.

Need to optimize:
- Calibrate distance with a known object at known distances.

## 2026-07-12 20:01:46 - Live camera test

- Duration: 5.9s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 23
- Beep candidate patterns: approach_ahead: 23
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 177
- Approx FPS: 30.2
- Background detection frames: 30
- Motion detection frames: 111
- Raw warning frames: 46
- Warning frames: 23
- Raw warning changes: 13
- Warning changes: 3
- Modes: guide: 177
- Sources: motion: 116, background: 33, none: 28
- Regions: middle_center: 82, clear: 28, bottom_center: 23, middle_left: 23, bottom_left: 7
- Closeness: far: 123, none: 28, medium: 26
- Risk levels: none: 99, low: 47, medium: 26, high: 5
- YOLO requested by config: True
- YOLO active: False
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a
- YOLO last error: No module named 'ultralytics'

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was requested by config.py, but it could not become active.

Need to optimize:
- Calibrate distance with a known object at known distances.
- Fix YOLO load error: No module named 'ultralytics'

## 2026-07-12 20:02:28 - Live camera test

- Duration: 3.1s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 3
- Beep candidate patterns: stop_ahead: 3
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 94
- Approx FPS: 30.4
- Background detection frames: 27
- Motion detection frames: 11
- Raw warning frames: 5
- Warning frames: 3
- Raw warning changes: 4
- Warning changes: 1
- Modes: guide: 94
- Sources: background: 52, none: 33, motion: 9
- Regions: middle_center: 35, clear: 33, middle_right: 13, bottom_left: 8, top_right: 4
- Closeness: far: 57, none: 33, medium: 2, close: 2
- Risk levels: none: 82, low: 9, high: 2, medium: 1
- YOLO requested by config: False
- YOLO active: False
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a
- YOLO last error: none

What we noticed:
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was disabled by config.py for this run.

Need to optimize:
- Calibrate distance with a known object at known distances.

## 2026-07-12 20:03:05 - Live camera test

- Duration: 14.4s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 28
- Beep candidate patterns: approach_ahead: 18, stop_ahead: 10
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 373
- Approx FPS: 25.9
- Background detection frames: 40
- Motion detection frames: 209
- Raw warning frames: 112
- Warning frames: 95
- Raw warning changes: 36
- Warning changes: 11
- Modes: guide: 373
- Sources: motion: 219, none: 96, background: 58
- Regions: clear: 96, middle_center: 76, middle_right: 62, middle_left: 41, bottom_center: 33
- Closeness: far: 192, none: 96, medium: 52, close: 33
- Risk levels: none: 248, low: 78, medium: 30, high: 17
- YOLO requested by config: False
- YOLO active: False
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 0
- YOLO final frames: 0
- YOLO inference runs: 0
- YOLO inference hits: 0
- YOLO cached returns: 0
- YOLO labels: none
- YOLO avg inference: n/a
- YOLO last inference: n/a
- YOLO last error: none

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was disabled by config.py for this run.

Need to optimize:
- Calibrate distance with a known object at known distances.

## 2026-07-12 20:06:44 - Live camera test

- Duration: 1.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 15
- Beep candidate patterns: stop_ahead: 10, approach_ahead: 5
- Background settle seconds: 0.1
- Background capture frames: 12
- Frames: 26
- Approx FPS: 26.0
- Background detection frames: 12
- Motion detection frames: 8
- Raw warning frames: 23
- Warning frames: 20
- Raw warning changes: 4
- Warning changes: 3
- Modes: guide: 26
- Sources: background: 23, motion: 2, none: 1
- Regions: bottom_center: 25, clear: 1
- Closeness: close: 15, medium: 8, far: 2, none: 1
- Risk levels: medium: 18, low: 5, none: 3
- YOLO requested by config: True
- YOLO active: True
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO Python executable: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\.venv-win\Scripts\python.exe
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 17
- YOLO final frames: 0
- YOLO inference runs: 2
- YOLO inference hits: 2
- YOLO cached returns: 15
- YOLO labels: person: 17
- YOLO avg inference: 138.0 ms
- YOLO last inference: 72.7 ms
- YOLO last error: none

What we noticed:
- Warnings appeared on most frames, so the detector is sensitive.
- The stabilizer reduced warning changes compared with raw detection.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Add smoothing/hysteresis so warnings do not feel jumpy.
- Calibrate distance with a known object at known distances.

## 2026-07-12 20:08:08 - Live camera test

- Duration: 30.2s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 82
- Beep candidate patterns: stop_ahead: 74, approach_ahead: 8
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 846
- Approx FPS: 28.0
- Background detection frames: 54
- Motion detection frames: 501
- Raw warning frames: 329
- Warning frames: 269
- Raw warning changes: 126
- Warning changes: 26
- Modes: guide: 846
- Sources: motion: 477, none: 278, background: 91
- Regions: clear: 278, middle_center: 137, middle_left: 99, middle_right: 88, bottom_center: 65
- Closeness: none: 278, far: 278, medium: 150, close: 140
- Risk levels: none: 595, low: 133, medium: 100, high: 18
- YOLO requested by config: True
- YOLO active: True
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO Python executable: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\.venv-win\Scripts\python.exe
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 787
- YOLO final frames: 0
- YOLO inference runs: 84
- YOLO inference hits: 79
- YOLO cached returns: 708
- YOLO labels: person: 547, chair: 240
- YOLO avg inference: 67.0 ms
- YOLO last inference: 138.0 ms
- YOLO last error: none

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 20:10:31 - Live camera test

- Duration: 100.0s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 148
- Beep candidate patterns: stop_ahead: 101, approach_ahead: 47
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 2380
- Approx FPS: 23.8
- Background detection frames: 291
- Motion detection frames: 814
- Raw warning frames: 508
- Warning frames: 380
- Raw warning changes: 189
- Warning changes: 37
- Modes: guide: 2380
- Sources: motion: 984, none: 819, background: 577
- Regions: clear: 819, bottom_left: 338, bottom_center: 289, middle_left: 221, middle_center: 190
- Closeness: far: 1126, none: 819, medium: 257, close: 178
- Risk levels: none: 1916, low: 304, medium: 118, high: 42
- YOLO requested by config: True
- YOLO active: True
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO Python executable: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\.venv-win\Scripts\python.exe
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 2191
- YOLO final frames: 0
- YOLO inference runs: 238
- YOLO inference hits: 220
- YOLO cached returns: 1971
- YOLO labels: person: 2031, chair: 160
- YOLO avg inference: 127.6 ms
- YOLO last inference: 127.4 ms
- YOLO last error: none

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-12 20:12:07 - Live camera test

- Duration: 69.8s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 118
- Beep candidate patterns: stop_ahead: 78, approach_ahead: 40
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 1694
- Approx FPS: 24.3
- Background detection frames: 353
- Motion detection frames: 573
- Raw warning frames: 772
- Warning frames: 652
- Raw warning changes: 187
- Warning changes: 46
- Modes: guide: 1694
- Sources: background: 651, motion: 632, none: 411
- Regions: middle_center: 605, clear: 411, bottom_center: 255, top_center: 136, top_right: 97
- Closeness: far: 563, medium: 557, none: 411, close: 163
- Risk levels: none: 1262, low: 254, medium: 146, high: 32
- YOLO requested by config: True
- YOLO active: True
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO Python executable: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\.venv-win\Scripts\python.exe
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 1135
- YOLO final frames: 0
- YOLO inference runs: 169
- YOLO inference hits: 114
- YOLO cached returns: 1021
- YOLO labels: person: 1135
- YOLO avg inference: 124.2 ms
- YOLO last inference: 120.3 ms
- YOLO last error: none

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

## 2026-07-13 18:08:18 - Live camera test

- Duration: 100.1s
- Camera index: 0
- Camera reported size: 320 x 240
- Processing size: 320 x 240
- Camera FPS reported: 30.0
- Audio output active: True
- Audio source: config.py
- Beep candidate frames: 32
- Beep candidate patterns: stop_ahead: 28, approach_ahead: 4
- Background settle seconds: 4.0
- Background capture frames: 12
- Frames: 2490
- Approx FPS: 24.9
- Background detection frames: 136
- Motion detection frames: 756
- Raw warning frames: 478
- Warning frames: 379
- Raw warning changes: 136
- Warning changes: 26
- Modes: guide: 2490
- Sources: none: 1214, motion: 992, background: 284
- Regions: clear: 1214, bottom_left: 633, middle_right: 186, bottom_center: 172, bottom_right: 76
- Closeness: none: 1214, far: 848, medium: 357, close: 71
- Risk levels: none: 2041, low: 333, medium: 91, high: 25
- YOLO requested by config: True
- YOLO active: True
- YOLO config file: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\config.py
- YOLO Python executable: C:\Users\dongx\OneDrive\Desktop\VisualGuideProject\.venv-win\Scripts\python.exe
- YOLO model path: yolo26n.pt
- YOLO confidence: 0.45
- YOLO process interval: 10
- YOLO allowlist: ('person', 'chair', 'car', 'bicycle')
- YOLO detection frames: 2431
- YOLO final frames: 0
- YOLO inference runs: 249
- YOLO inference hits: 244
- YOLO cached returns: 2187
- YOLO labels: person: 2431
- YOLO avg inference: 112.9 ms
- YOLO last inference: 114.5 ms
- YOLO last error: none

What we noticed:
- Frame-to-frame motion detection was the strongest signal in this run.
- The stabilizer reduced warning changes compared with raw detection.
- Stabilized warning text still changed often during the run.
- Approach-risk grading detected medium/high risk movement trends.
- Approximate distance values were produced, but they still need calibration.
- Audio output was active through config.py.
- Some stable warnings matched the beep policy.
- YOLO was enabled; compare YOLO inference timing against total camera FPS.

Need to optimize:
- Tune stabilizer settings and motion sensitivity further.
- Calibrate distance with a known object at known distances.

