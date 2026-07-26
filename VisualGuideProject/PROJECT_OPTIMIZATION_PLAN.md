# Visual Guide Robot Optimization Plan

## Project understanding

This project is a visual obstacle guidance prototype. It reads camera frames,
detects obstacles, estimates where they are in the camera view, and prints or
speaks warnings. The intended help is early obstacle awareness for a moving
robot or assistive visual guide system.

## 1. Audio delay plan

Current finding:

- `pyttsx3.runAndWait()` blocks on Windows, so spoken audio can freeze or delay
  the camera loop.
- Linux speech uses `espeak-ng` through a subprocess, which is better, but
  speech can still be too slow for fast safety warnings.

Current code action:

- Added `AUDIO_OUTPUT_MODE = "beep"` as a lightweight option.
- Audio remains disabled by default with `AUDIO_ENABLED = False`.
- Beep mode is now gated to avoid noise:
  - approaching danger ahead
  - YOLO-recognized vehicle warnings for `car` or `bicycle`
- Beep mode repeats no faster than once every `2.0` seconds.
- Added differentiated beep patterns:
  - approaching ahead: medium double beep
  - stop/approaching ahead: fast triple beep
  - car warning: lower double beep
  - bicycle warning: higher quick double beep
- Added `audio_alert_api.py` so pattern playback stays separate from warning
  decision logic.

Future plan:

- On Raspberry Pi, first test with audio disabled, then enable beep mode after
  camera FPS is acceptable.
- Later, use a GPIO buzzer or small speaker for urgent beeps.
- On Linux/Pi, pattern mode can use `aplay` with generated tiny WAV files; if
  unavailable, it falls back to terminal bell.
- Keep speech only for low-urgency status messages, not emergency obstacle
  warnings.
- If speech is needed, move it to a dedicated output queue/thread so the camera
  loop never waits for speech.

## 2. Moving-object sensitivity plan

Current issue:

- Background subtraction can lock onto static scene changes.
- It does not specifically know whether an object is actively moving.

Current code action:

- Added frame-to-frame moving-object detection in `vision_api.py`.
- Lowered background thresholds for more sensitivity.
- Combined background, motion, and YOLO candidates in continuous guide mode.
- Prioritized center and lower-frame detections.
- Background capture now uses a multi-frame median after an exposure-settle
  period.
- After the guide-mode live test, raised frame-to-frame motion thresholds to
  reduce warning chatter:
  - `MOTION_OBJECT_MIN_AREA = 450`
  - `MOTION_OBJECT_THRESHOLD_VALUE = 18`

Future plan:

- Test on the saved MP4 and on the real camera.
- Tune `MOTION_OBJECT_MIN_AREA`, `MOTION_OBJECT_THRESHOLD_VALUE`, and
  `BACKGROUND_PROCESS_INTERVAL`.
- Add object tracking if boxes still flicker or jump.
- Use `DetectionStabilizer` settings to balance responsiveness against calm
  warning output.

## 3. YOLO on Raspberry Pi 4 plan

Research summary:

- Current Ultralytics docs focus on YOLO26. Their Raspberry Pi guide recommends
  exported edge formats, especially NCNN on ARM devices.
- Raspberry Pi 4 can run small nano YOLO models, but full PyTorch YOLO at normal
  image sizes will likely cause delay if it runs every frame.
- Start with a nano model, low image size, and low inference frequency.

Current code action:

- YOLO is now enabled for controlled laptop testing.
- Added optional `requirements-yolo.txt`.
- Updated YOLO first target to `yolo26n.pt`; if the installed package cannot
  load YOLO26 yet, use `yolo11n.pt` or `yolov8n.pt`.
- Added `YOLO_IMAGE_SIZE = 320`.
- Added `YOLO_STALE_FRAMES` so old YOLO boxes do not stay forever.
- Added class danger weights and optional class filtering.
- Added YOLO inference timing/logging to the live camera test.
- First laptop no-window test on camera index `0` reached `26.8 FPS` with YOLO
  average inference at `84.2 ms` while running every 10 frames.
- After the first visible test, changed YOLO from a dominant warning source to a
  recognition helper:
  - first classes: `person`, `chair`, `car`, `bicycle`
  - `YOLO_USE_AS_WARNING_SOURCE = False`
  - YOLO can label a motion/background warning candidate
  - YOLO-only detections do not warn by themselves

Future plan:

- Repeat a visible-window YOLO test with `person`, `chair`, `car`, and
  `bicycle` examples.
- Decide later whether any class should be allowed to warn from YOLO alone.
- Export to NCNN on Raspberry Pi before trying continuous camera use.
- Run YOLO every 5-10 frames while the fast motion/background detector runs
  every frame or every 2 frames.
- Consider a Coral TPU, Pi 5, or lighter model if Pi 4 latency is too high.

Useful source:

- https://docs.ultralytics.com/guides/raspberry-pi
- https://docs.ultralytics.com/modes/export

## 4. Distance detection plan

Current limitation:

- A single normal camera cannot measure true distance by itself without
  calibration, known object size, or another sensor.

Current code action:

- Added `distance_api.py` for approximate monocular distance.
- Debug overlay can show estimated distance.
- Warning messages do not speak distance by default because uncalibrated
  distance can be misleading.

Future plan:

- Calibrate with a known object width at known distances.
- Prefer adding real distance hardware for safer real distance:
  - Ultrasonic sensor such as HC-SR04/HC-SR04P for cheap center distance.
  - Time-of-flight sensor such as VL53L1X for short-range I2C distance.
  - Stereo/depth camera such as OAK-D/DepthAI or Intel RealSense for richer
    per-pixel depth.
- Use distance mainly for center-region objects first.

Package notes:

- `gpiozero.DistanceSensor` supports HC-SR04-style ultrasonic sensors on
  Raspberry Pi GPIO.
- `adafruit-circuitpython-vl53l1x` supports the VL53L1X time-of-flight sensor
  on Raspberry Pi/Linux.
- Luxonis DepthAI devices provide stereo depth and spatial AI pipelines, but
  require different camera code from regular OpenCV webcam input.

## 5. 9-region design plan

Current code action:

- Added 3 x 3 region judging.
- Debug view now draws a 9-region grid.
- Priority logic treats lower-center objects as more dangerous.

Future plan:

- Add region-specific warning language only after testing.
- Example future warnings: "low center obstacle", "upper right object", or
  "path blocked center".
- Use bottom-center and middle-center as the strongest collision zones.

## 6. Display/testing plan

Current display behavior:

- Normal testing shows one final decision box by default.
- Raw detector boxes can still be shown by setting
  `SHOW_ALL_DETECTION_SOURCES = True` in `config.py`.

Box colors:

- Final decision box: yellow
- Background raw box: green
- Motion raw box: orange
- YOLO raw box: purple

## 7. Stability plan

Current code action:

- Added `DetectionStabilizer` to smooth the selected final box.
- Added warning hysteresis so non-urgent warning text must persist before
  changing.
- Urgent center-stop warnings still pass quickly.
- After the guide-mode live test, reduced stale-box/stale-warning hold time and
  made non-urgent warning text changes slightly stricter.

Future plan:

- Tune `WARNING_STABLE_FRAMES`, `CLEAR_STABLE_FRAMES`, and
  `WARNING_CHANGE_MIN_SECONDS` from real camera tests.
- If warning changes remain high, add simple object tracking with IDs and
  region-specific hysteresis.

## 8. Background Capture Plan

Current code action:

- Background capture waits briefly for exposure to settle.
- It collects several empty-view frames.
- It builds the saved background with a median image by default.
- Background-difference detections now pass through a persistence filter before
  they are allowed to trigger the final warning.

Future plan:

- Tune `BACKGROUND_SETTLE_SECONDS` and `BACKGROUND_CAPTURE_FRAMES` per camera.
- Tune `BACKGROUND_DETECTION_STABLE_FRAMES` per camera. Higher values reduce
  false background boxes but delay real static-obstacle warnings slightly.
- Add automatic stability scoring before accepting a background.
- If a camera still drifts after capture, consider adaptive background updates
  only while the view is clear.

## 9. Code Simplification Plan

Current code action:

- Replaced explicit standby/moving behavior with one continuous `guide` loop.
- Added `detection_api.py` so the app and live test share the same detection
  pipeline.
- Added `visual_guide_runtime.py` so the continuous guide session is shared by
  laptop launcher and Raspberry Pi production launcher.
- Added `pi_visual_guide.py` for camera-gated Pi production mode.
- Removed the old mode-switch rollback code after guide-mode testing:
  - deleted `mode_manager.py`
  - removed legacy mode config values
  - removed old unused helper functions

Future plan:

- Split `LIVE_CAMERA_TEST.py` into smaller files only if it becomes harder to
  maintain.

## 10. Raspberry Pi Production Plan

Current code action:

- Added Pi standby/camera-gate behavior:
  - no camera: wait in terminal standby
  - camera plugged in: start continuous guide
  - camera unplugged: stop session and return to standby
- Added shell scripts:
  - `start_visual_guide_pi.sh`
  - `install_pi_autostart.sh`
- `LIVE_CAMERA_TEST.py` remains a laptop/timed test tool.
- Pi production mode uses `pi_visual_guide.py` and has no 25-second timer.

Future plan:

- Test autostart on actual Raspberry Pi desktop.
- If Raspberry Pi desktop ignores `Terminal=true`, adjust autostart script for
  the installed terminal app.

## 11. Approach-Risk Grading Plan

Current code action:

- Added `risk_api.py` with `ApproachRiskTracker`.
- Uses 9-region movement, box area growth, rough distance trend, and speed to
  decide whether an object is approaching.
- Far objects can become caution warnings only when the risk trend is medium or
  high.
- Random side-to-side crossing without size/distance growth is capped at low
  risk.
- After the guide-mode live test, approach-risk thresholds were tightened so
  medium/high risk requires stronger size, distance, speed, or path evidence.

Future plan:

- Tune risk thresholds from live camera tests:
  - `APPROACH_RISK_MIN_AREA_GROWTH`
  - `APPROACH_RISK_STRONG_AREA_GROWTH`
  - `APPROACH_RISK_FAST_SPEED_RATIO`
- Add background flow compensation after the current risk layer is tested.
- Later, use YOLO object labels to weight risk differently for people, cars,
  bicycles, chairs, bags, and walls.
