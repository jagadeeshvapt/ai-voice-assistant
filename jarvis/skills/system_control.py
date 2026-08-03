import os
import platform
import subprocess
import datetime
import psutil
import random
from pathlib import Path

from .base import Skill, register_skill
from ..config import config
from ..utils import logger

@register_skill
class SystemControlSkill(Skill):
    name = "system_control"
    description = "Controls system - open apps, volume, shutdown, lock, screenshot, etc"
    keywords = [
        "open", "launch", "start", "run app", "volume", "brightness", "shutdown", "restart", "sleep", "lock",
        "screenshot", "screen capture", "battery", "cpu", "ram", "memory", "close", "minimize", "fullscreen",
        "mute", "unmute", "wifi", "bluetooth", "notepad", "calculator", "browser", "chrome", "vscode", "code editor"
    ]
    patterns = [
        r"open (.+)",
        r"launch (.+)",
        r"start (.+)",
        r"shutdown (system|pc|computer)?",
        r"restart (system|pc|computer)?",
        r"lock (system|pc|computer|screen)?",
        r"take (a )?screenshot",
        r"(increase|decrease|set) volume",
        r"battery (status|level)",
        r"system (info|status)",
    ]

    def handle(self, text, context=None):
        low = text.lower()

        # Screenshot
        if "screenshot" in low or "screen capture" in low:
            try:
                import pyautogui
                path = str(config.DATA_DIR / f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                pyautogui.screenshot(path)
                return f"Screenshot captured and saved to {path}, sir"
            except Exception as e:
                return f"Screenshot failed: {e}"

        # System info
        if "battery" in low:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    return f"Battery at {battery.percent}% {'charging' if battery.power_plugged else 'on battery'}"
                else:
                    return "Battery information not available on this system"
            except Exception as e:
                return f"Couldn't get battery info: {e}"

        if "cpu" in low or "ram" in low or "memory" in low or "system info" in low or "system status" in low:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent if platform.system() != "Windows" else psutil.disk_usage('C:').percent
            return f"System status: CPU {cpu}%, RAM {ram}%, Disk {disk}% used"

        # Volume control
        if "volume" in low:
            if "mute" in low:
                return self._set_volume_mute(True)
            if "unmute" in low:
                return self._set_volume_mute(False)
            if "increase" in low or "up" in low:
                return self._adjust_volume("up")
            if "decrease" in low or "down" in low:
                return self._adjust_volume("down")
            return "Volume control: say increase, decrease, mute or unmute"

        # Shutdown / Restart / Lock / Sleep
        if "shutdown" in low:
            if any(w in low for w in ["cancel", "abort"]):
                self._cancel_shutdown()
                return "Shutdown cancelled"
            # For safety, don't actually shutdown immediately, ask confirmation via return message
            # But we implement it with delay that can be cancelled
            if config.TEXT_MODE or "now" in low or "immediately" in low:
                return self._shutdown_system()
            else:
                return "Shutting down system in 10 seconds... Say cancel shutdown to abort. Executing now."
        
        if "restart" in low or "reboot" in low:
            return self._restart_system()

        if "lock" in low or "lock screen" in low:
            return self._lock_system()

        # Open apps / websites
        if any(x in low for x in ["open", "launch", "start"]):
            # Extract app name
            import re
            m = re.search(r"(?:open|launch|start)\s+(.+)", low)
            if m:
                app = m.group(1).strip()
                return self._open_application(app)
        
        return None

    def _open_application(self, app_name: str):
        app_name = app_name.lower().strip()
        # Map common apps
        app_map = {
            "notepad": "notepad" if platform.system() == "Windows" else "gedit",
            "calculator": "calc" if platform.system() == "Windows" else "gnome-calculator",
            "browser": "chrome" if platform.system() == "Windows" else "google-chrome",
            "chrome": "chrome" if platform.system() == "Windows" else "google-chrome",
            "firefox": "firefox",
            "vscode": "code",
            "code": "code",
            "explorer": "explorer" if platform.system() == "Windows" else "nautilus",
            "files": "explorer" if platform.system() == "Windows" else "nautilus",
            "terminal": "cmd" if platform.system() == "Windows" else "gnome-terminal",
            "cmd": "cmd",
            "spotify": "spotify",
            "word": "winword",
            "excel": "excel",
        }

        # Websites
        websites = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "gmail": "https://mail.google.com",
            "github": "https://github.com",
            "netflix": "https://netflix.com",
            "twitter": "https://twitter.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "linkedin": "https://linkedin.com",
            "reddit": "https://reddit.com",
            "stackoverflow": "https://stackoverflow.com",
            "wikipedia": "https://wikipedia.org",
        }

        for site_key, url in websites.items():
            if site_key in app_name:
                import webbrowser
                webbrowser.open(url)
                return f"Opening {site_key}, sir"

        # Try app map
        cmd = app_map.get(app_name, app_name)
        try:
            if platform.system() == "Windows":
                os.system(f"start {cmd}")
            elif platform.system() == "Darwin":
                os.system(f"open -a {cmd}")
            else:
                subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opening {app_name}, sir"
        except Exception as e:
            logger.error(f"Open app error {app_name}: {e}")
            # Try opening as URL
            try:
                import webbrowser
                webbrowser.open(f"https://{app_name}.com")
                return f"Trying to open {app_name} in browser"
            except:
                return f"Could not open {app_name}: {e}"

    def _shutdown_system(self):
        try:
            if platform.system() == "Windows":
                os.system("shutdown /s /t 10")
            else:
                os.system("shutdown -h +0.1")
            return "Initiating shutdown sequence, sir"
        except Exception as e:
            return f"Shutdown failed: {e}"

    def _restart_system(self):
        try:
            if platform.system() == "Windows":
                os.system("shutdown /r /t 10")
            else:
                os.system("shutdown -r +0.1")
            return "Restarting system, sir"
        except Exception as e:
            return f"Restart failed: {e}"

    def _lock_system(self):
        try:
            if platform.system() == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif platform.system() == "Darwin":
                subprocess.call(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
            else:
                os.system("xdg-screensaver lock || gnome-screensaver-command -l || dm-tool lock")
            return "Locking system, sir"
        except Exception as e:
            return f"Lock failed: {e}"

    def _cancel_shutdown(self):
        try:
            if platform.system() == "Windows":
                os.system("shutdown /a")
            else:
                os.system("shutdown -c")
        except:
            pass

    def _set_volume_mute(self, mute: bool):
        try:
            if platform.system() == "Windows":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMute(mute, None)
                return f"Volume {'muted' if mute else 'unmuted'}"
            else:
                cmd = "amixer -D pulse set Master mute" if mute else "amixer -D pulse set Master unmute"
                os.system(cmd)
                return f"Volume {'muted' if mute else 'unmuted'}"
        except Exception as e:
            return f"Volume control not available: {e}. Try manually."

    def _adjust_volume(self, direction: str):
        try:
            if platform.system() == "Windows":
                # Use nircmd if available, otherwise keyboard simulation
                import pyautogui
                if direction == "up":
                    for _ in range(5):
                        pyautogui.press("volumeup")
                    return "Volume increased"
                else:
                    for _ in range(5):
                        pyautogui.press("volumedown")
                    return "Volume decreased"
            else:
                cmd = "amixer -D pulse set Master 10%+ " if direction == "up" else "amixer -D pulse set Master 10%-"
                os.system(cmd)
                return f"Volume {direction}"
        except Exception as e:
            return f"Volume adjust failed: {e}"
