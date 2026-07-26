# Code Optimization Record

## 2026-07-11 - Correctness and clarity pass

This pass intentionally preserves the project's existing camera, warning, motion,
and detection design. It fixes control-flow defects without changing the public
API of any module.

### `main.py`

- Initialized background detection collections and masks on every loop. Previously,
  `background_detections` could be used before it had been assigned, which could
  stop the program on the first frame.
- Added persistent `last_background_detections` and `last_background_mask` state.
  Background processing still runs only at the configured interval, while drawing
  and guidance safely reuse the most recent result between processing frames.
- Stored the chosen standby background detection in `last_background_detection`.
  Previously, the selected detection was immediately overwritten by combining an
  unchanged `None` value with the YOLO result, so background warnings were lost.
- Made moving-mode fallback use the same multi-object detection and priority
  selection path as standby mode.
- Made the mask window read from the separately stored mask instead of assuming a
  primary detection exists. A useful mask can now be displayed even when no
  contour passes the object filters.
- Replaced hard-coded `0.25` and `0.10` priority thresholds with
  `CLOSE_AREA_RATIO` and `MEDIUM_AREA_RATIO` from `config.py`.
- Removed the unused `draw_detection` import.

### `config.py`

- Removed duplicate definitions of `PRINT_ENABLED`, `SHOW_DEBUG_WINDOWS`,
  `SHOW_DETECTION_MASK`, and `YOLO_ENABLED`.
- Removed the earlier conflicting `MOVING_FALLBACK_TO_BACKGROUND = False`.
  The existing later value, `True`, remains the single active setting. Be aware
  that background differencing while the camera moves can cause false warnings;
  set it to `False` after YOLO is enabled and working reliably.

### Behavior deliberately not changed

- Warning wording and cooldown timing.
- Camera resolution, frame dropping, and motion thresholds.
- Background-difference and YOLO algorithms.
- Audio remains disabled by default.

### Hardware validation checklist

1. Start with an empty, stable camera view for background capture.
2. Confirm standby mode detects a newly introduced object without crashing.
3. Confirm boxes remain visible between background-processing intervals.
4. Move the camera long enough to enter moving mode, then hold it still long
   enough to return to standby and recapture the background.
5. If moving mode gives false warnings while YOLO is disabled, set
   `MOVING_FALLBACK_TO_BACKGROUND = False`.

## 2026-07-11 - Detection priority and loop optimization pass

This pass keeps the same prototype architecture, but tightens several runtime
behaviors that can affect safety, delay, and tuning clarity.

### `main.py`

- Changed final detection fusion so YOLO no longer automatically overrides
  background-difference detection. The code now chooses the most dangerous
  candidate by closeness, center position, and size across both sources.
- Added a size tie-breaker to primary detection selection. When two objects
  have the same danger bucket, the larger one wins consistently.
- Cleared cached background detections when entering moving mode. This avoids
  carrying an old standby obstacle into moving-mode fallback.
- Made safety warnings interrupt mode announcements and older speech, matching
  the existing comment in the code.
- Moved debug overlay drawing inside the `SHOW_DEBUG_WINDOWS` branch so the
  main loop avoids unnecessary drawing work when debug windows are disabled.

### `output_api.py` and `mode_manager.py`

- Switched warning cooldown and mode-switch timing from wall-clock time to
  monotonic time. This avoids timing glitches if the system clock changes.

### `guidance_api.py`

- Matched closeness threshold boundaries with the detection-priority logic by
  using `>=` for close and medium thresholds.
- Clamped multi-object labels so text does not draw above the visible frame.

## 2026-07-11 - Moving-object, region, distance, and audio planning pass

This pass starts adapting the prototype toward a more practical visual guide
robot design while keeping YOLO and audio disabled by default.

### `config.py`

- Added `AUDIO_OUTPUT_MODE = "beep"` and beep timing settings. Audio remains
  disabled unless `AUDIO_ENABLED` is set to `True`.
- Lowered background-difference sensitivity thresholds for faster obstacle
  response: smaller contour area, lower threshold, smaller blur kernel, and
  background processing every 2 frames.
- Added frame-to-frame moving-object detection settings.
- Added 3 x 3 region grid settings.
- Added approximate monocular distance calibration settings.
- Added YOLO performance settings: smaller `YOLO_IMAGE_SIZE` and
  `YOLO_STALE_FRAMES`.

### `vision_api.py`

- Added a separate frame-to-frame moving-object detector. This catches objects
  that are actively moving, instead of relying only on differences from the
  captured background.
- Shared contour extraction logic between background and moving-object
  detection.
- Reset the moving-object baseline whenever a new background is captured.

### `guidance_api.py`

- Added `judge_region()` for a 3 x 3 region layout while keeping the older
  left/center/right warning language.
- Updated debug grid drawing from 3 vertical regions to 9 regions.
- Colored boxes by detection source: background, motion, or YOLO.

### `distance_api.py`

- Added approximate monocular distance estimation based on bounding-box width,
  camera field of view, and an assumed real object width.
- Added formatting helper for debug display.

### `main.py`

- Combined background, moving-object, and YOLO detections in standby mode.
- Prioritized lower-frame and center detections because they are more likely to
  be in the robot/user path.
- Added motion-source priority when detections are otherwise similar.
- Added debug overlay for region, approximate distance, and detection source.

### `output_api.py`

- Added a non-blocking beep mode for urgent ahead/stop warnings.
- Kept speech mode available, but separated it from beep mode so future testing
  can avoid `pyttsx3` camera-loop blocking.

### `warning_api.py`

- Added optional distance text for center warnings. It is disabled by default
  through `INCLUDE_DISTANCE_IN_WARNING = False` until distance calibration is
  tested.

## 2026-07-11 - Live camera test follow-up

Live test summary:

- Camera opened successfully at `320 x 240`, `30 FPS`.
- Test processed 251 frames in 25.1 seconds, around 10.0 FPS while printing
  detailed diagnostics.
- Background detection appeared on 80 frames.
- Frame-to-frame moving-object detection appeared on 208 frames.
- Warning logic produced warnings on 197 frames.
- Region logic reported positions such as `bottom_center`, `bottom_left`, and
  `bottom_right`.
- Approximate distance estimates appeared, for example around `0.7 m` to
  `1.9 m` for large close face detections.

Code follow-up:

- Moving mode now also uses the frame-to-frame motion detector. During the live
  test, motion detection remained useful after mode switched to moving, so the
  real app should keep using it there too.

## 2026-07-11 - Test display simplification pass

- Added `SHOW_ALL_DETECTION_SOURCES` to `config.py`.
- Normal debug/test display now shows one yellow final decision box instead of
  drawing background and motion boxes at the same time.
- Raw background/motion/YOLO boxes are still available by setting
  `SHOW_ALL_DETECTION_SOURCES = True`.
- Added source-aware final labels such as `FINAL motion`.
- Updated the project plan and test log with distance hardware options and box
  color meanings.

## 2026-07-11 - New camera test follow-up

Live test finding:

- Camera index `1` opened successfully and appears to be the newly attached
  camera.
- The camera reported `640 x 480` even though the project requested
  `320 x 240`.
- This made the detector more sensitive/noisy than expected because several
  tuning values are based on the configured low-resolution processing size.

Code follow-up:

- `CameraAPI.get_frame()` now resizes frames to `FRAME_WIDTH x FRAME_HEIGHT`
  after capture if the camera/backend ignores the requested resolution.
  This keeps detection thresholds and processing speed more consistent across
  laptop webcam, USB camera, and Raspberry Pi camera testing.
- Windows camera startup now prefers the DirectShow backend before falling back
  to OpenCV's default backend. This is usually more stable for USB webcams than
  the default MSMF backend.
- Frame reads now retry briefly before failing, which helps with camera startup
  and quick reopen cases.

## 2026-07-11 - Warning and box stability pass

Problem:

- Live tests showed high warning churn. The detector was sensitive, but warning
  text changed too quickly between left/right/center, caution/stop, and clear.

Code changes:

- Added `stability_api.py` with `DetectionStabilizer`.
- Added stability settings to `config.py`.
- Smoothed the final selected bounding box with exponential smoothing.
- Held the last stable box briefly across short detection misses.
- Required non-urgent warning text to persist for a few frames before changing.
- Allowed urgent center `Stop. obstacle ahead.` warnings to pass immediately.
- Updated `main.py` to stabilize the final box and warning before display/output.
- Updated `LIVE_CAMERA_TEST.py` to print both raw and stabilized warnings.
- Fixed the live-test overlay so source/region/closeness/distance/warning text
  appears again.

Validation:

- Syntax check passed.
- Stabilizer probe showed non-urgent warnings require three consistent frames.
- A 10-second available-camera test showed raw warning changes reduced from
  `12` to stabilized warning changes of `3`.

Camera note:

- When rescanned, only camera index `0` was visible to OpenCV. The previous
  USB camera at index `1` was not available during the stabilizer test.

## 2026-07-11 - Robust background capture pass

Problem:

- Camera index `1` produced many background detections after capture. The likely
  causes were auto-exposure settling, lighting shifts, and capturing the
  background from one unlucky frame.

Code changes:

- Added background capture settings to `config.py`.
- Added `background_api.py` with `capture_stable_background()`.
- Added `VisionAPI.capture_background_from_frames()`.
- Background is now built from multiple empty-view frames using a median image
  by default.
- The real app now uses stable multi-frame background capture on startup and
  when returning to standby.
- `LIVE_CAMERA_TEST.py` now shows background-settle and capture progress, and
  logs the settle time and frame count.
- Added `DetectionPersistenceFilter` for background-difference detections.
  A green/background candidate now has to appear consistently before it can
  drive the final warning, which filters short camera-drift ghosts.

Expected effect:

- Fewer false green/background boxes after background capture.
- More fair tests between camera index `0`, camera index `1`, and future
  Raspberry Pi cameras.
- In the index `1` no-window test, raw warning frames dropped from `78 / 182`
  after median-only capture to `32 / 182` after the persistence filter.

## 2026-07-11 - Continuous guide mode simplification

Problem:

- The old standby/moving mode switch made the detection path more complicated.
- The camera should keep checking moving objects whether the robot/user is
  moving or not.
- YOLO integration will be easier if there is one continuous detection pipeline
  instead of separate standby and moving branches.

Code changes:

- Added `detection_api.py` with `ContinuousDetectionPipeline`.
- Rewrote `main.py` around one `GUIDE_MODE = "guide"` loop.
- Updated `LIVE_CAMERA_TEST.py` to use the same detection pipeline as the app.
- Marked `mode_manager.py` and old standby/moving config values as legacy
  rollback code, not active app behavior.
- Added `CODE_REVIEW_MILESTONE.md` with a file-by-file cleanup audit.

Expected effect:

- Less branching in the main camera loop.
- Fewer confusing mode announcements.
- More readable path for enabling YOLO later.

## 2026-07-11 - Approach-risk grading pass

Problem:

- Exact monocular distance is not accurate enough yet.
- A static distance estimate misses an important safety question: whether the
  object is moving into the user's path and getting larger/closer.

Code changes:

- Added `risk_api.py` with `ApproachRiskTracker`.
- Added approach-risk config values in `config.py`.
- `main.py` now attaches approach-risk grades to the final detection and passes
  the risk level into warning generation.
- `warning_api.py` can now upgrade a far object into a caution warning when its
  trend is medium/high risk.
- `LIVE_CAMERA_TEST.py` now displays, prints, and logs risk levels.
- Added `APPROACH_RISK_DESIGN.md`.

Validation:

- Synthetic left-to-center + larger + closer object graded as `high`.
- Synthetic fast side crossing with no size/distance growth stayed `low`.

Future:

- Add background flow compensation: track stable background points, estimate
  shared camera/background motion, and treat objects moving differently from
  that background flow as higher risk.

## 2026-07-11 - Post guide-mode live-test tuning pass

Problem:

- The 20-second camera index `1` guide-mode test stayed fast at about `22.5`
  FPS, but motion detection was active on `415 / 450` frames.
- Warnings appeared on `353 / 450` frames.
- Raw warning text changed `171` times, and stabilized warning text still
  changed `21` times.

Code changes:

- Made frame-to-frame motion detection less sensitive:
  - `MOTION_OBJECT_MIN_AREA`: `250` -> `450`
  - `MOTION_OBJECT_THRESHOLD_VALUE`: `12` -> `18`
- Made approach-risk grading stricter:
  - `APPROACH_RISK_MIN_AREA_GROWTH`: `0.08` -> `0.12`
  - `APPROACH_RISK_STRONG_AREA_GROWTH`: `0.20` -> `0.28`
  - `APPROACH_RISK_DISTANCE_DROP_RATIO`: `0.12` -> `0.16`
  - `APPROACH_RISK_FAST_SPEED_RATIO`: `0.035` -> `0.045`
  - `APPROACH_RISK_MEDIUM_SCORE`: `3` -> `4`
  - `APPROACH_RISK_HIGH_SCORE`: `5` -> `6`
- Made stale detections/warnings clear sooner but non-urgent text change more
  slowly:
  - `DETECTION_HOLD_FRAMES`: `4` -> `2`
  - `WARNING_STABLE_FRAMES`: `3` -> `4`
  - `CLEAR_STABLE_FRAMES`: `5` -> `3`
  - `WARNING_CHANGE_MIN_SECONDS`: `0.7` -> `0.9`

Validation:

- Python syntax validation passed.
- Synthetic approaching object still grades as `high`.
- Synthetic sideways crossing without size growth still stays `low`.

## 2026-07-12 - Legacy mode cleanup pass

Decision:

- Continuous `GUIDE_MODE = "guide"` is now the active behavior.
- The old standby/walking mode-switch system is no longer kept as rollback code.

Code changes:

- Deleted `mode_manager.py`.
- Removed unused legacy config values:
  - `MOTION_THRESHOLD`
  - `MODE_SWITCH_SECONDS`
  - `MODE_MOVING`
  - `MODE_STANDBY`
  - `MOVING_FALLBACK_TO_BACKGROUND`
- Removed old helper functions that active code no longer used:
  - `guidance_api.draw_detection()`
  - `vision_api.detect_obstacle()`

Validation:

- Confirmed no remaining Python references to the removed names.
- Python syntax validation passed.
- `main`, `LIVE_CAMERA_TEST`, `config`, `vision_api`, and `guidance_api`
  import successfully.

## 2026-07-12 - YOLO integration preparation pass

Decision:

- Prepare the code for YOLO testing without enabling YOLO or installing heavy
  dependencies yet.

Code changes:

- Added optional `requirements-yolo.txt`.
- Changed first YOLO target to `YOLO_MODEL_PATH = "yolo26n.pt"`, with comments
  explaining fallback to `yolo11n.pt` or `yolov8n.pt` if needed.
- Set safer initial YOLO cadence:
  - `YOLO_PROCESS_INTERVAL = 10`
  - `YOLO_STALE_FRAMES = 10`
- Added YOLO class danger weights and optional class allowlist in `config.py`.
- Reworked `yolo_vision_api.py` to support:
  - class allowlist
  - class danger weighting
  - detection priority score
  - cached detections between YOLO inference frames
  - inference timing stats
  - load/error stats
- Updated `detection_api.py` so YOLO priority can influence tie-breaking
  without automatically overriding closer OpenCV detections.
- Updated `LIVE_CAMERA_TEST.py` to print and log YOLO metrics.
- Added `YOLO_INTEGRATION_PLAN.md`.

Validation:

- YOLO remains disabled by default.
- Python syntax validation passed.
- `YOLOVisionAPI().get_stats()` works while YOLO is disabled.
- Main app and live test imports pass.

## 2026-07-12 - YOLO install and first camera test

Decision:

- Enable YOLO for controlled testing on the Windows laptop using a conservative
  inference cadence.

Code/environment changes:

- Installed base `ultralytics` package in `.venv-win`.
- Downloaded and loaded `yolo26n.pt`.
- Redirected Ultralytics settings to the project folder with `YOLO_CONFIG_DIR`
  so it does not require AppData access.
- Redirected Matplotlib cache to `MatplotlibCache/` for the same reason.
- Updated `.gitignore` for generated YOLO/runtime artifacts:
  - `Ultralytics/`
  - `MatplotlibCache/`
  - `runs/`
  - `*.pt`
  - `*_ncnn_model/`
- Changed `requirements-yolo.txt` to install base `ultralytics` first. The
  heavier `[export]` extra remains a later Raspberry Pi/export step.
- Set `YOLO_ENABLED = True`.

Validation:

- `ultralytics` imports successfully.
- `yolo26n.pt` loads successfully.
- Synthetic blank-frame inference runs successfully.
- Live no-window camera test on index `0` completed:
  - `26.8 FPS`
  - YOLO average inference: `84.2 ms`
  - YOLO ran every 10 frames
  - YOLO produced the final detection on most frames
- Camera index `1` was not available during this run.

Next tuning note:

- YOLO did not cause severe laptop delay at the current cadence, but it is very
  influential in the final decision. Next tests should verify whether YOLO
  should always trigger warnings for static semantic obstacles, or mostly act
  as a label/risk helper for motion/background detections.

## 2026-07-12 - YOLO recognition + existing danger warning fusion

Decision:

- Use YOLO as an object-recognition feature first.
- Keep the danger warning authority with the existing background/motion,
  distance, 9-region, and approach-risk logic.

Code changes:

- Limited YOLO recognition to the first target classes:
  - `person`
  - `chair`
  - `car`
- Added `YOLO_USE_AS_WARNING_SOURCE = False`.
- Added YOLO-to-warning-candidate matching using box overlap or center distance.
- Updated the detector fusion so:
  - motion/background detections can become warning candidates
  - YOLO can attach `label`, `confidence`, and recognition metadata to that
    candidate
  - YOLO-only detections do not create warnings by themselves
- Updated the display helpers:
  - final warning box remains yellow
  - YOLO recognition box remains purple
  - a combined final box can display text like `FINAL background + person`
- Updated live test logs to record YOLO recognized labels.

Validation:

- Python syntax validation passed for all project `.py` files.
- Synthetic fusion check passed: a background candidate overlapping a YOLO
  `person` keeps source `background` and receives label `person`.
- Short empty-view no-window camera test completed:
  - `28.5 FPS`
  - YOLO inference runs: `28`
  - YOLO labels: `none`
  - warning frames: `0`
- Visible fusion test completed:
  - `29.5 FPS`
  - YOLO final frames: `0`
  - YOLO labels: `person: 380`, `chair: 280`
  - warning frames: `310`
- Fixed `LIVE_CAMERA_TEST.py` so test warnings pass the recognized label into
  `make_warning()`, matching the main app behavior.

Next tuning note:

- Run a visible test with a person/chair/car entering the view. The expected
  behavior is that YOLO recognizes the class, but warnings only happen when the
  existing danger logic sees motion/background change and risk/closeness.

## 2026-07-12 - Quiet safety beep policy

Decision:

- Keep audio lightweight for Raspberry Pi.
- Use short beep warnings only for selected danger cases, not every warning.

Beep rules:

1. Beep when a warning says an obstacle is `approaching ... ahead`.
2. Beep when YOLO recognition helps produce a moving vehicle warning:
   - `car`
   - `bicycle`

Code changes:

- Added `bicycle` to `YOLO_CLASS_ALLOWLIST`.
- Changed beep repeat limit to `BEEP_REPEAT_SECONDS = 2.0`.
- Added configurable beep gates:
  - `BEEP_ON_APPROACHING_AHEAD`
  - `BEEP_ON_VEHICLE_WARNING`
  - `BEEP_VEHICLE_LABELS`
- Updated `warning_api.py` so a close center object with medium/high approach
  risk says `Stop. approaching <object> ahead.`
- Updated `output_api.py` so:
  - stable warning text still avoids print/speech spam
  - beep output can repeat every 2 seconds while the same danger continues
  - ordinary side/static warnings stay silent

Validation:

- Python syntax validation passed.
- Beep gate checks:
  - `Caution. approaching person ahead.` -> beep
  - `Stop. approaching obstacle ahead.` -> beep
  - `Stop. person ahead.` -> no beep
  - `Caution. car on right.` -> beep
  - `Caution. bicycle on left.` -> beep
  - `Caution. obstacle on right.` -> no beep

Current note:

- `AUDIO_ENABLED` is still `False` by default. Turn it on only when we want an
  audio test:

```python
AUDIO_ENABLED = True
AUDIO_OUTPUT_MODE = "beep"
```

## 2026-07-12 - Differentiated beep-pattern audio layer

Decision:

- Add different beep patterns for different safety events.
- Avoid heavy sound packages before Raspberry Pi testing.
- Keep playback non-blocking so camera FPS is protected.

Pattern design:

- `approach_ahead`: medium double beep
- `stop_ahead`: faster triple beep
- `vehicle_car`: lower double beep
- `vehicle_bicycle`: higher quick double beep
- ordinary warnings: silent

Code changes:

- Added `audio_alert_api.py`.
- Moved pattern playback into `AudioAlertPlayer`.
- Windows uses built-in `winsound.Beep`.
- Linux/Raspberry Pi tries `aplay` with small generated `.wav` files.
- If `aplay` is unavailable, Linux falls back to terminal bell.
- Added `audio_cache/` to `.gitignore` for generated Pi/Linux WAV files.
- Updated `output_api.py` to classify stable warnings into beep patterns:
  - `approach_ahead`
  - `stop_ahead`
  - `vehicle_car`
  - `vehicle_bicycle`

Validation:

- Python syntax validation passed.
- Dry pattern classification:
  - `Caution. approaching person ahead.` -> `approach_ahead`
  - `Stop. approaching obstacle ahead.` -> `stop_ahead`
  - `Stop. person ahead.` -> no beep
  - `Caution. car on right.` -> `vehicle_car`
  - `Caution. bicycle on left.` -> `vehicle_bicycle`
  - `Caution. obstacle on right.` -> no beep

## 2026-07-12 - Laptop camera test with temporary audio enabled

Decision:

- Add an audio test switch to `LIVE_CAMERA_TEST.py` instead of permanently
  enabling audio in `config.py`.

Code changes:

- Added `set_audio_override()` to `output_api.py`.
- Added `--audio` to `LIVE_CAMERA_TEST.py`.
- During an audio test, stable warnings are routed through `output_warning()`.
- After the test finishes, the audio override is reset to normal config
  behavior.

Validation:

- Python syntax validation passed.
- `LIVE_CAMERA_TEST.py --help` shows the new `--audio` option.
- Visible laptop camera test with temporary audio enabled completed:
  - `29.5 FPS`
  - YOLO enabled
  - YOLO labels: `person: 561`
  - warning frames: `424`
  - audio test enabled: `True`

Observation:

- The new audio path did not noticeably reduce camera FPS on the laptop.
- Terminal still prints every stable warning when `PRINT_ENABLED = True`; this
  is separate from the beep gate. Beeps remain limited by the pattern rules and
  `BEEP_REPEAT_SECONDS = 2.0`.

## 2026-07-12 - Re-test after removing standalone audio demo

Decision:

- Keep only the real camera-flow audio test path:
  - `LIVE_CAMERA_TEST.py --audio`
- Remove standalone beep-demo testing from the workflow.

Validation:

- Visible laptop camera test with temporary audio enabled was run again.
- Test was stopped early by the user after `18.3s`.
- Result:
  - `29.2 FPS`
  - YOLO enabled
  - YOLO labels: `person: 496`
  - warning frames: `351`
  - audio test enabled
- Beep-eligible stable warnings appeared during the run, including:
  - `Stop. approaching person ahead.`
  - `Stop. approaching obstacle ahead.`

Observation:

- The audio-enabled camera test still did not noticeably reduce camera FPS.
- Future improvement: log beep-pattern counts separately from terminal
  `WARNING:` text output so audio tests are easier to verify from logs.

## 2026-07-12 - Raspberry Pi production runner and camera gate

Decision:

- Keep `LIVE_CAMERA_TEST.py` as a timed laptop/test tool.
- Add a Pi production entrypoint with no test timer.
- Add a camera-plug gate so the Pi can boot before the camera is connected.

Code changes:

- Added `visual_guide_runtime.py`:
  - shared continuous visual-guide session
  - no time limit
  - returns clear session status when camera is lost or user quits
- Simplified `main.py` to call the shared runtime.
- Added `pi_visual_guide.py`:
  - standby loop when no camera is available
  - starts guide session when camera is plugged in
  - returns to standby when camera is unplugged
- Added `camera_is_available()` to `camera_api.py`.
- Added Pi camera-gate config:
  - `CAMERA_WAIT_RETRY_SECONDS`
  - `CAMERA_STANDBY_PRINT_SECONDS`
- Added `start_visual_guide_pi.sh`.
- Added `install_pi_autostart.sh`.

Pi behavior:

- On boot into desktop, the autostart script can open the Pi terminal.
- Before camera is plugged in: standby.
- After camera is plugged in: continuous guide starts.
- After camera is unplugged: guide stops and returns to standby.
- There is no 25-second timer in Pi production mode.

Validation:

- Python syntax validation passed.
- `main`, `pi_visual_guide`, and `visual_guide_runtime` import successfully.

## 2026-07-12 - Laptop live-test audio/YOLO diagnostics

Problem:

- `config.py` could say `AUDIO_ENABLED = True`, but `LIVE_CAMERA_TEST.py`
  only called audio output when the command included `--audio`.
- YOLO load failures were not printed clearly in the live-test summary.

Code changes:

- `LIVE_CAMERA_TEST.py` now treats `AUDIO_ENABLED = True` as active audio.
- `--audio` remains as a force-on override for one test run.
- Live-test summaries now print:
  - audio active/source
  - beep-eligible warning frame count
  - beep pattern counts
  - YOLO last error
- `output_api.py` exposes `classify_beep_pattern()` for diagnostics.
- `yolo_vision_api.py` now forces Ultralytics config files into the project
  `Ultralytics/` folder to avoid Windows AppData permission errors.

## 2026-07-12 - Make YOLO controlled clearly by config.py

Problem:

- It was too easy to see `YOLO_ENABLED = True` in `config.py` but not know
  whether YOLO was actually active, failed to load, or only running as a
  recognition layer.

Code changes:

- `yolo_vision_api.py` now reads YOLO settings directly from `config.py`.
- YOLO startup prints the exact config file path and key settings:
  - `YOLO_ENABLED`
  - model path
  - confidence
  - process interval
- `LIVE_CAMERA_TEST.py` summary now separates:
  - YOLO requested by config
  - YOLO actually active
  - YOLO load error
- `detection_api.py` now reads YOLO warning/matching settings from `config.py`
  directly, instead of copying those values during import.

Control rule:

- `YOLO_ENABLED = True` in `config.py` means the program must try to load and
  run YOLO.
- `YOLO_ENABLED = False` means the program does not run YOLO.
- If YOLO is requested but fails, the terminal and test log now show the reason.

## 2026-07-12 - Fix laptop YOLO missing ultralytics environment issue

Problem:

- The live test could be launched by a Python environment that did not have
  `ultralytics` installed, causing:
  - `YOLO could not be loaded: No module named 'ultralytics'`
- This was not a config failure. `YOLO_ENABLED = True` was working, but the
  selected Python environment was wrong.

Code changes:

- Added Windows laptop environment controls in `config.py`:
  - `WINDOWS_PROJECT_VENV_ENABLED`
  - `WINDOWS_PROJECT_VENV_PYTHON`
- `LIVE_CAMERA_TEST.py` now automatically restarts itself with the project
  `.venv-win` Python on Windows before importing OpenCV/YOLO.
- `LIVE_CAMERA_TEST.py` prints the Python executable used for the test.
- `yolo_vision_api.py` prints the Python executable used for YOLO loading.

Expected result:

- Running `LIVE_CAMERA_TEST.py` from a wrong Python should switch into
  `.venv-win` automatically.
- YOLO should then find the already installed `ultralytics` package.
