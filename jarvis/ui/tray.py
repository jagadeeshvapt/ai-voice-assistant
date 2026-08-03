"""
JARVIS UI - Tray App, system tray icon
Uses pystray if available, otherwise dummy
"""
from typing import Optional
from ..config import config
from ..utils import logger

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

class TrayApp:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self._icon = None
        self._running = False

    def _create_image(self):
        # Simple JARVIS icon - blue circle
        if PYSTRAY_AVAILABLE:
            try:
                img = Image.new('RGB', (64, 64), color=(10, 15, 28))
                draw = ImageDraw.Draw(img)
                draw.ellipse((8, 8, 56, 56), outline=(0, 212, 255), width=3)
                draw.ellipse((20, 20, 44, 44), fill=(0, 255, 255))
                return img
            except:
                pass
        return None

    def _on_show(self, icon, item):
        logger.info("Tray show requested")

    def _on_quit(self, icon, item):
        icon.stop()
        if self.orchestrator:
            self.orchestrator.stop()

    def run(self):
        if not PYSTRAY_AVAILABLE:
            logger.info("Tray not available (install pystray + pillow)")
            return
        
        try:
            image = self._create_image()
            menu = pystray.Menu(
                pystray.MenuItem("Show Dashboard", self._on_show),
                pystray.MenuItem("Quit JARVIS", self._on_quit)
            )
            self._icon = pystray.Icon("JARVIS", image, "JARVIS Local Assistant", menu)
            self._running = True
            self._icon.run()
        except Exception as e:
            logger.error(f"Tray run failed: {e}")

    def stop(self):
        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except:
                pass

def get_tray_app(orchestrator=None):
    return TrayApp(orchestrator)
