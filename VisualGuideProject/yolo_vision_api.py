# yolo_vision_api.py

import os
import sys
import time
from pathlib import Path

import config


class YOLOVisionAPI:
    def __init__(self):
        self.config_path = str(Path(config.__file__).resolve())
        self.requested_enabled = bool(config.YOLO_ENABLED)
        self.enabled = self.requested_enabled
        self.model = None
        self.frame_counter = 0
        self.last_detection = None
        self.last_detection_frame = 0
        self.last_error = None
        self.last_inference_ms = None
        self.total_inference_ms = 0.0
        self.inference_runs = 0
        self.inference_hits = 0
        self.cached_returns = 0
        self.last_raw_box_count = 0
        self.last_allowed_box_count = 0

        print(
            "YOLO config: "
            f"YOLO_ENABLED={self.requested_enabled}, "
            f"model={config.YOLO_MODEL_PATH}, "
            f"conf={config.YOLO_CONFIDENCE}, "
            f"interval={config.YOLO_PROCESS_INTERVAL}, "
            f"config_file={self.config_path}, "
            f"python={sys.executable}"
        )

        if not self.requested_enabled:
            print("YOLO is disabled by config.py. Using OpenCV motion/background detection.")
            return

        try:
            project_dir = Path(__file__).resolve().parent
            yolo_config_dir = project_dir / "Ultralytics"
            matplotlib_config_dir = project_dir / "MatplotlibCache"
            yolo_config_dir.mkdir(exist_ok=True)
            matplotlib_config_dir.mkdir(exist_ok=True)

            # Keep Ultralytics/Matplotlib runtime files inside this project.
            # This avoids permission errors when Windows blocks writes to the
            # default AppData config folder.
            os.environ["YOLO_CONFIG_DIR"] = str(yolo_config_dir)
            os.environ["MPLCONFIGDIR"] = str(matplotlib_config_dir)

            from ultralytics import YOLO

            self.model = YOLO(config.YOLO_MODEL_PATH)
            print(f"YOLO model loaded: {config.YOLO_MODEL_PATH}")

        except Exception as error:
            self.last_error = str(error)
            print(f"YOLO could not be loaded: {error}")
            print(f"YOLO Python executable: {sys.executable}")
            if isinstance(error, ModuleNotFoundError) and error.name == "ultralytics":
                print(
                    "YOLO dependency is missing from this Python. "
                    "On the Windows laptop, run LIVE_CAMERA_TEST.py through "
                    "the project .venv-win environment."
                )
            print("YOLO will be disabled.")
            self.enabled = False

    def detect_object(self, frame):
        """
        Detect object using YOLO.

        Return:
            detection dictionary or None
        """

        if not self.enabled or self.model is None:
            return None

        self.frame_counter += 1

        process_interval = max(1, config.YOLO_PROCESS_INTERVAL)
        if self.frame_counter % process_interval != 0:
            return self._get_cached_detection()

        start_time = time.perf_counter()

        try:
            results = self.model(
                frame,
                verbose=False,
                conf=config.YOLO_CONFIDENCE,
                imgsz=config.YOLO_IMAGE_SIZE,
            )
        except Exception as error:
            self.last_error = str(error)
            self.last_detection = None
            return None
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.last_inference_ms = elapsed_ms
            self.total_inference_ms += elapsed_ms
            self.inference_runs += 1

        detection = self._select_best_detection(results)
        self.last_detection = detection

        if detection is not None:
            self.inference_hits += 1
            self.last_detection_frame = self.frame_counter

        return detection

    def get_stats(self):
        average_ms = None
        if self.inference_runs > 0:
            average_ms = self.total_inference_ms / self.inference_runs

        return {
            "config_enabled": self.requested_enabled,
            "enabled": self.enabled,
            "model_path": config.YOLO_MODEL_PATH,
            "confidence": config.YOLO_CONFIDENCE,
            "process_interval": config.YOLO_PROCESS_INTERVAL,
            "image_size": config.YOLO_IMAGE_SIZE,
            "allowlist": config.YOLO_CLASS_ALLOWLIST,
            "config_path": self.config_path,
            "python_executable": sys.executable,
            "inference_runs": self.inference_runs,
            "inference_hits": self.inference_hits,
            "cached_returns": self.cached_returns,
            "last_inference_ms": self.last_inference_ms,
            "average_inference_ms": average_ms,
            "last_raw_box_count": self.last_raw_box_count,
            "last_allowed_box_count": self.last_allowed_box_count,
            "last_error": self.last_error,
        }

    def _get_cached_detection(self):
        if (
            self.last_detection is not None
            and self.frame_counter - self.last_detection_frame <= config.YOLO_STALE_FRAMES
        ):
            self.cached_returns += 1
            cached_detection = self.last_detection.copy()
            cached_detection["cached"] = True
            return cached_detection

        return None

    def _select_best_detection(self, results):
        if not results:
            self.last_raw_box_count = 0
            self.last_allowed_box_count = 0
            return None

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            self.last_raw_box_count = 0
            self.last_allowed_box_count = 0
            return None

        self.last_raw_box_count = len(result.boxes)
        self.last_allowed_box_count = 0
        best_detection = None
        best_score = None

        for box in result.boxes:
            detection = self._box_to_detection(box)

            if detection is None:
                continue

            if not self._is_allowed_label(detection["label"]):
                continue

            self.last_allowed_box_count += 1
            selection_score = (
                detection["danger_weight"],
                detection["confidence"],
                detection["box_area"],
            )

            if best_score is None or selection_score > best_score:
                best_score = selection_score
                best_detection = detection

        return best_detection

    def _box_to_detection(self, box):
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        x = int(x1)
        y = int(y1)
        w = int(x2 - x1)
        h = int(y2 - y1)

        box_area = w * h

        if box_area <= 0:
            return None

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        label = self._get_label(class_id)
        danger_weight = self._get_danger_weight(label)
        cx = x + w // 2
        cy = y + h // 2

        return {
            "bbox": (x, y, w, h),
            "center": (cx, cy),
            "box_area": box_area,
            "label": label,
            "confidence": confidence,
            "danger_weight": danger_weight,
            "priority_score": int(danger_weight * 10),
            "source": "yolo",
            "mask": None,
        }

    def _get_label(self, class_id):
        names = self.model.names

        if isinstance(names, dict):
            return names.get(class_id, str(class_id))

        if 0 <= class_id < len(names):
            return names[class_id]

        return str(class_id)

    def _is_allowed_label(self, label):
        if not config.YOLO_CLASS_ALLOWLIST:
            return True

        allowed = {item.lower() for item in config.YOLO_CLASS_ALLOWLIST}
        return label.lower() in allowed

    def _get_danger_weight(self, label):
        return config.YOLO_CLASS_DANGER_WEIGHTS.get(
            label.lower(),
            config.YOLO_DEFAULT_CLASS_DANGER_WEIGHT,
        )
