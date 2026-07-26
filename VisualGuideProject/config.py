# config.py

# =========================
# User control panel
# =========================

# =========================
# Laptop Python environment
# =========================

# Windows laptop helper:
# True = LIVE_CAMERA_TEST.py automatically uses the project virtual environment.
# This keeps YOLO controllable from this project instead of depending on a
# random Python selected by Windows, PowerShell, VS Code, or another terminal.
WINDOWS_PROJECT_VENV_ENABLED = True
WINDOWS_PROJECT_VENV_PYTHON = ".venv-win\\Scripts\\python.exe"

# True  = enable beep/speech output
# False = no audio output
AUDIO_ENABLED = True

# Audio mode when AUDIO_ENABLED is True:
# "speech" = spoken warnings
# "beep"   = short non-blocking beep for ahead/stop warnings
AUDIO_OUTPUT_MODE = "beep"

# True  = print warnings in terminal
# False = do not print warnings
PRINT_ENABLED = True

# Show main camera/debug window.
SHOW_DEBUG_WINDOWS = True

# Show black/white detection mask window.
# False is better for speed.
SHOW_DETECTION_MASK = False

# Show every raw detector box at once.
# False = show only the final decision box, clearer for normal testing.
# True  = show background/motion/YOLO boxes together for debugging.
SHOW_ALL_DETECTION_SOURCES = False

# Enable YOLO object detection.
# Enabled after the first Windows install/load test.
# Keep the process interval conservative to protect camera responsiveness.
YOLO_ENABLED = True

#-----------------

# =========================
# Camera settings
# =========================

CAMERA_INDEX = 0

# Pi production mode camera gate.
# The Pi runner waits in standby until this camera can be opened.
CAMERA_WAIT_RETRY_SECONDS = 2.0
CAMERA_STANDBY_PRINT_SECONDS = 5.0

# Lower resolution helps reduce delay.
# If image quality is too poor, change back to 640 x 480.
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
CAMERA_FPS = 30

# Drop old frames before reading the current frame.
# If video feels delayed, increase to 2 or 3.
# If video becomes unstable, set back to 0 or 1.
DROP_OLD_FRAMES = 2

# =========================
# Detection sensitivity
# =========================

# If detection is too weak, decrease this.
# If too many small things are detected, increase this.
MIN_CONTOUR_AREA = 550

# If detection is too weak, decrease this.
# If detection is too noisy, increase this.
THRESHOLD_VALUE = 14

# Blur must be an odd number: 3, 5, 7, 11, 21.
# Smaller = more sensitive.
# Larger = smoother but less sensitive.
BLUR_KERNEL_SIZE = 7

# More dilation connects broken regions but may make boxes too large.
DILATION_ITERATIONS = 1

# Reject detections that cover too much of the frame.
# This prevents camera movement from becoming one huge center object.
MAX_DETECTION_AREA_RATIO = 0.65


# =========================
# Background-difference detection settings
# =========================

# Let the camera auto-exposure settle before saving the empty background.
BACKGROUND_SETTLE_SECONDS = 1.0

# Build the saved background from several frames instead of one frame.
# Median is robust against a brief moving object during capture.
BACKGROUND_CAPTURE_FRAMES = 12
BACKGROUND_CAPTURE_FRAME_DELAY_SECONDS = 0.03
BACKGROUND_CAPTURE_METHOD = "median"

# Run background detection every N frames.
# 1 = every frame, more accurate but slower.
# 2 = every 2 frames, faster.
BACKGROUND_PROCESS_INTERVAL = 2

# Background-difference boxes must persist this many processed cycles before
# they can drive the final warning. This reduces false boxes from camera drift.
BACKGROUND_DETECTION_STABLE_FRAMES = 2


# =========================
# Moving-object detection settings
# =========================

# Frame-to-frame moving-object detection is separate from background detection.
# It helps catch objects that are actively moving toward/through the camera view.
MOTION_OBJECT_DETECTION_ENABLED = True
MOTION_OBJECT_PROCESS_INTERVAL = 1
MOTION_OBJECT_MIN_AREA = 450
MOTION_OBJECT_THRESHOLD_VALUE = 18
MOTION_OBJECT_BLUR_KERNEL_SIZE = 5
MOTION_OBJECT_DILATION_ITERATIONS = 1
MOTION_OBJECT_MAX_AREA_RATIO = 0.45


# =========================
# Closeness estimation settings
# =========================

# These values estimate closeness based on bounding-box area ratio.
# This is not real physical distance.
CLOSE_AREA_RATIO = 0.25
MEDIUM_AREA_RATIO = 0.10

# =========================
# Multi-object detection
# =========================

# Maximum number of moving/changing objects to track.
MAX_OBJECTS = 5


# =========================
# Region grid settings
# =========================

# 3 x 3 gives nine regions: top/middle/bottom and left/center/right.
REGION_GRID_ROWS = 3
REGION_GRID_COLS = 3


# =========================
# Approximate distance settings
# =========================

# Monocular distance is only an estimate until calibrated.
# Formula uses object image width, camera field of view, and an assumed real width.
DISTANCE_ESTIMATION_ENABLED = True
CAMERA_HORIZONTAL_FOV_DEGREES = 62.0
DISTANCE_REFERENCE_WIDTH_M = 0.45
INCLUDE_DISTANCE_IN_WARNING = False

# =========================
# Approach-risk grading settings
# =========================

# Use movement history to decide whether an object is really approaching.
# This uses region movement, bounding-box growth, speed, and rough distance
# trend as a danger grade. It does not require perfectly accurate meters.
APPROACH_RISK_ENABLED = True
APPROACH_RISK_HISTORY_FRAMES = 8

# Box area growth between the oldest and newest tracked observation.
APPROACH_RISK_MIN_AREA_GROWTH = 0.12
APPROACH_RISK_STRONG_AREA_GROWTH = 0.28

# Rough distance trend. Since monocular distance is approximate, this is only
# one vote in the risk grade.
APPROACH_RISK_DISTANCE_DROP_RATIO = 0.16

# Center movement speed as a fraction of frame diagonal per frame.
APPROACH_RISK_FAST_SPEED_RATIO = 0.045

# Score boundaries.
APPROACH_RISK_MEDIUM_SCORE = 4
APPROACH_RISK_HIGH_SCORE = 6

# =========================
# Audio warning settings
# =========================

# Beep settings. A short beep is much cheaper than speech in the camera loop.
# Current safety-beep policy:
# 1. beep when an obstacle is approaching ahead
# 2. beep when a YOLO-recognized vehicle warning mentions car/bicycle
BEEP_ONLY_FOR_AHEAD = False
BEEP_FREQUENCY_HZ = 880
BEEP_DURATION_MS = 120
BEEP_REPEAT_SECONDS = 2.0
BEEP_ON_APPROACHING_AHEAD = True
BEEP_ON_VEHICLE_WARNING = True
BEEP_VEHICLE_LABELS = ("car", "bicycle")

# Beep pattern sounds. Each item is (frequency_hz, duration_ms).
# Use frequency 0 for a short silence gap.
# Keep patterns short so audio never feels noisy and never burdens the camera.
BEEP_PATTERN_APPROACH_AHEAD = ((880, 120), (0, 80), (880, 120))
BEEP_PATTERN_STOP_AHEAD = ((960, 90), (0, 60), (960, 90), (0, 60), (960, 90))
BEEP_PATTERN_CAR = ((520, 150), (0, 80), (520, 150))
BEEP_PATTERN_BICYCLE = ((1250, 80), (0, 60), (1250, 80))
BEEP_PATTERN_DEFAULT = ((BEEP_FREQUENCY_HZ, BEEP_DURATION_MS),)


# =========================
# Guide mode setting
# =========================

# Current default behavior is one continuous guide mode.
GUIDE_MODE = "guide"


# =========================
# YOLO settings
# =========================

# YOLO model file.
# yolo26n.pt = current Ultralytics nano model, best first target if supported
# by the installed ultralytics package.
# If your package cannot load YOLO26 yet, set this to "yolo11n.pt" or
# "yolov8n.pt" for compatibility testing.
YOLO_MODEL_PATH = "yolo26n.pt"

# Minimum confidence for YOLO detection.
YOLO_CONFIDENCE = 0.45

# Run YOLO every N frames to reduce delay.
# 1 = every frame, slower.
# 10 = every 10 frames, safer first test for laptop/Pi.
YOLO_PROCESS_INTERVAL = 10

# Lower image size is important on Raspberry Pi class hardware.
YOLO_IMAGE_SIZE = 320

# Do not keep old YOLO boxes forever between slow inference frames.
YOLO_STALE_FRAMES = 10

# YOLO is currently used as an object-recognition layer first.
# Start with the classes we want to study in this project stage.
YOLO_CLASS_ALLOWLIST = ("person", "chair", "car", "bicycle")

# False = YOLO can label a warning candidate, but it does not create a warning
# by itself. This keeps yesterday's motion/background/risk warning behavior.
YOLO_USE_AS_WARNING_SOURCE = False

# Match a YOLO label to a motion/background candidate when the boxes overlap
# or their centers are close enough.
YOLO_LABEL_MATCH_IOU_THRESHOLD = 0.05
YOLO_LABEL_MATCH_CENTER_DISTANCE_RATIO = 0.22

# Class danger weights help choose between multiple YOLO boxes and break ties
# inside the YOLO recognition layer. Labels not listed use the default.
YOLO_DEFAULT_CLASS_DANGER_WEIGHT = 1.0
YOLO_CLASS_DANGER_WEIGHTS = {
    "person": 2.0,
    "bicycle": 2.4,
    "car": 2.5,
    "motorcycle": 2.5,
    "bus": 2.5,
    "truck": 2.5,
    "chair": 1.5,
    "bench": 1.4,
    "backpack": 1.2,
    "suitcase": 1.2,
    "dog": 1.3,
}


# =========================
# Warning optimization
# =========================

# Smooth the final selected detection box and warning text.
STABILITY_ENABLED = True

# Higher = follows movement faster. Lower = smoother but slower.
BOX_SMOOTHING_ALPHA = 0.45

# Decide whether a new box is probably the same target as the previous box.
BOX_MATCH_IOU_THRESHOLD = 0.10
BOX_MATCH_CENTER_DISTANCE_RATIO = 0.28

# Keep the last stable box briefly when detection flickers for a few frames.
DETECTION_HOLD_FRAMES = 2

# Require non-urgent warning text to persist before changing output.
WARNING_STABLE_FRAMES = 4

# Urgent center-stop warnings can pass immediately.
URGENT_WARNING_STABLE_FRAMES = 1

# Require a few clear frames before removing the current warning.
CLEAR_STABLE_FRAMES = 3

# Avoid rapid non-urgent warning text changes.
WARNING_CHANGE_MIN_SECONDS = 0.9

# Do not repeat the same normal warning too often.
SAME_WARNING_REPEAT_SECONDS = 8.0

# Urgent stop warning can repeat, but still not too frequently.
URGENT_WARNING_REPEAT_SECONDS = 5.0

# If no warning is detected for this time, allow same warning again later.
WARNING_RESET_SECONDS = 1.5
