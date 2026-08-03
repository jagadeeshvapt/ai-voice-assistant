"""
JARVIS Tools - Screenshots + OCR (Tesseract offline)
"""
from typing import Dict
from datetime import datetime
from pathlib import Path
from .registry import Tool
from ..config import config
from ..utils import logger

class ScreenshotTool(Tool):
    name = "take_screenshot"
    description = "Takes screenshot and saves to data"
    dangerous = False
    required_permission = 1

    def validate(self, args):
        pass

    def execute(self, args):
        try:
            import pyautogui
            fname = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            save_path = config.DATA_DIR / fname
            save_path.parent.mkdir(parents=True, exist_ok=True)
            pyautogui.screenshot(str(save_path))
            
            # Try OCR if requested
            if "read" in (args.get("raw") or "").lower() or "ocr" in (args.get("raw") or "").lower():
                text = self._ocr_image(save_path)
                return f"Screenshot eduthuten at {save_path}. OCR text: {text[:500]}"
            
            return f"Screenshot eduthuten: {save_path}"
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return f"Screenshot edukka mudiyala: {e}"

    def _ocr_image(self, image_path: Path) -> str:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text[:1000] if text else "No text found"
        except Exception as e:
            logger.debug(f"OCR failed: {e}")
            return "OCR not available (install tesseract)"
