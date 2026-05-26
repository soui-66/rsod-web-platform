import threading
import time
from typing import Optional, Dict, Any
import cv2
import numpy as np

from app.config import settings
from ultralytics import YOLO

class DetectionStatus:
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class CameraDetectionService:
    _instance: Optional['CameraDetectionService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._status = DetectionStatus.STOPPED
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._detection_thread = None
        
        self._confidence_threshold = 0.5
        self._iou_threshold = 0.7
        self._model_image_size = 320
        
        self._max_concurrent_requests = 5
        self._request_semaphore = threading.Semaphore(self._max_concurrent_requests)
        
        self._frame_count = 0
        self._fps_frame_count = 0
        self._last_fps_time = time.time()
        
        self._model = None
        self._class_names = {}
        
        self._initialized = True

    @property
    def is_running(self):
        return self._status == DetectionStatus.RUNNING

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        with self._lock:
            self._status = value

    def start_detection(self, camera_id: int = 0, confidence_threshold: float = 0.5, 
                       iou_threshold: float = 0.7, inference_interval: int = 2) -> bool:
        if self.is_running:
            self.stop_detection()

        try:
            self._stop_event.clear()
            self._pause_event.clear()
            
            self._confidence_threshold = confidence_threshold
            self._iou_threshold = iou_threshold
            
            self._frame_count = 0
            self._fps_frame_count = 0
            self._last_fps_time = time.time()
            
            # 加载 YOLO 模型
            self._model = YOLO(settings.yolo_model_path)
            self._class_names = self._model.names

            self.status = DetectionStatus.RUNNING
            return True

        except Exception as e:
            from app.utils.logger import logger
            logger.error(f"启动摄像头检测失败: {str(e)}")
            self.status = DetectionStatus.ERROR
            return False

    def stop_detection(self):
        if self.status == DetectionStatus.STOPPED:
            return

        self._stop_event.set()

        if self._detection_thread is not None:
            self._detection_thread.join(timeout=3.0)
            self._detection_thread = None

        self.status = DetectionStatus.STOPPED

    def pause_detection(self):
        if self.is_running:
            self._pause_event.set()
            self.status = DetectionStatus.PAUSED

    def resume_detection(self):
        if self.status == DetectionStatus.PAUSED:
            self._pause_event.clear()
            self.status = DetectionStatus.RUNNING

    def detect_image(self, image: np.ndarray) -> Dict[str, Any]:
        with self._request_semaphore:
            start_time = time.time()

            if self._model is None:
                return {
                    "boxes": [],
                    "frame_index": self._frame_count,
                    "fps": 0,
                    "detection_time": 0,
                    "total_objects": 0
                }

            results = self._model.predict(
                source=image,
                conf=self._confidence_threshold,
                iou=self._iou_threshold,
                save=False,
                imgsz=self._model_image_size,
                half=False,
                verbose=False,
                stream=False
            )

            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self._class_names.get(class_id, f"class_{class_id}")
                    
                    boxes.append({
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": class_name,
                        "chinese_name": class_name
                    })

            detection_time = time.time() - start_time

            self._frame_count += 1
            self._fps_frame_count += 1
            current_time = time.time()
            elapsed = current_time - self._last_fps_time
            
            fps = 0.0
            if elapsed >= 1.0:
                fps = self._fps_frame_count / elapsed
                self._fps_frame_count = 0
                self._last_fps_time = current_time

            return {
                "boxes": boxes,
                "frame_index": self._frame_count,
                "fps": fps,
                "detection_time": detection_time,
                "total_objects": len(boxes)
            }

camera_detection_service = CameraDetectionService()