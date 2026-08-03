"""
JARVIS Vision - Camera, face detection, object awareness
"""
import threading
import time
from typing import Optional, List, Dict

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

import numpy as np

from .config import config
from .utils import logger

class Vision:
    def __init__(self):
        self.enabled = config.ENABLE_VISION and CV2_AVAILABLE
        self.camera_index = config.CAMERA_INDEX
        self.cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.last_frame = None
        self.faces_detected = 0
        self.face_cascade = None
        
        if self.enabled:
            try:
                # Haar cascade for face detection
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                logger.info("Vision: Face detector loaded")
            except Exception as e:
                logger.error(f"Vision init face cascade error: {e}")
                self.face_cascade = None
        else:
            if not CV2_AVAILABLE:
                logger.info("Vision disabled - opencv not available")
            else:
                logger.info("Vision disabled in config (.env ENABLE_VISION=true to enable)")

    def start(self):
        if not self.enabled:
            return False
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Could not open camera {self.camera_index}")
                self.enabled = False
                return False
            
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            logger.info("Vision camera started")
            return True
        except Exception as e:
            logger.error(f"Vision start error: {e}")
            return False

    def _loop(self):
        while self._running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                self.last_frame = frame
                
                # Face detection
                if self.face_cascade is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    self.faces_detected = len(faces)
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Vision loop error: {e}")
                time.sleep(0.5)

    def stop(self):
        self._running = False
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
        logger.info("Vision stopped")

    def get_status(self) -> str:
        if not self.enabled:
            return "Vision system offline (enable in .env)"
        if not self._running:
            return "Vision idle"
        if self.faces_detected == 0:
            return "Scanning... no faces detected"
        elif self.faces_detected == 1:
            return "1 person in view"
        else:
            return f"{self.faces_detected} people in view"

    def capture_image(self, save_path: str = None) -> Optional[str]:
        if not self.enabled or self.last_frame is None:
            return None
        try:
            if save_path is None:
                import datetime
                save_path = str(config.DATA_DIR / f"capture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            cv2.imwrite(save_path, self.last_frame)
            return save_path
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return None

    def describe_scene(self) -> str:
        """Return a textual description of what camera sees"""
        if not self.enabled:
            return "Vision is disabled. Enable it in .env to get visual awareness."
        
        if not self._running:
            self.start()
            time.sleep(1)
        
        if self.faces_detected == 0:
            return "I don't see anyone in front of the camera right now."
        elif self.faces_detected == 1:
            return "I can see you in front of the camera."
        else:
            return f"I can see {self.faces_detected} people in view."

    def take_screenshot(self) -> Optional[str]:
        """Take desktop screenshot using pyautogui"""
        try:
            import pyautogui
            import datetime
            path = str(config.DATA_DIR / f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            pyautogui.screenshot(path)
            return path
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

# Singleton
vision_instance: Optional[Vision] = None

def get_vision() -> Vision:
    global vision_instance
    if vision_instance is None:
        vision_instance = Vision()
    return vision_instance
