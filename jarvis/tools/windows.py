"""
JARVIS Tools - Windows OS Control, strict offline, safe commands only
"""
import os
import platform
import subprocess
from typing import Dict
from .registry import Tool
from ..config import config
from ..utils import logger

class WindowsControlTool(Tool):
    name = "windows_control"
    description = "Windows system controls - lock, shutdown, restart, sleep, etc with safety"
    dangerous = True
    required_permission = 3

    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    def validate(self, arguments: Dict):
        # No unrestricted shell if ALLOW_SHELL false
        if not config.ALLOW_SHELL and arguments.get("shell_command"):
            raise ValueError("Shell commands disabled for safety (ALLOW_SHELL=false)")

    def execute(self, arguments: Dict):
        raw = (arguments.get("raw") or "").lower()
        intent = arguments.get("intent") or arguments.get("_intent") or self.name
        
        # Determine action from intent or raw
        if "shutdown" in intent or "shutdown" in raw:
            return self._shutdown()
        if "restart" in intent or "restart" in raw or "reboot" in raw:
            return self._restart()
        if "sleep" in intent or "sleep" in raw or "hibernate" in raw:
            return self._sleep()
        if "lock" in intent or "lock" in raw:
            return self._lock()
        
        return "Windows control - specify shutdown, restart, sleep, or lock"

    def _shutdown(self):
        try:
            if platform.system() == "Windows":
                os.system("shutdown /s /t 10")
            else:
                os.system("shutdown -h +0.1 2>/dev/null || systemctl poweroff 2>/dev/null")
            return "Shutdown start panniten Sir, 10 seconds la. Cancel panna 'abort shutdown' sollunga."
        except Exception as e:
            return f"Shutdown failed: {e}"

    def _restart(self):
        try:
            if platform.system() == "Windows":
                os.system("shutdown /r /t 10")
            else:
                os.system("shutdown -r +0.1 2>/dev/null || systemctl reboot 2>/dev/null")
            return "Restart initiate panniten Sir."
        except Exception as e:
            return f"Restart failed: {e}"

    def _sleep(self):
        try:
            if platform.system() == "Windows":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            else:
                os.system("systemctl suspend 2>/dev/null || pm-suspend 2>/dev/null")
            return "Sleep mode ku poren Sir."
        except Exception as e:
            return f"Sleep failed: {e}"

    def _lock(self):
        try:
            if platform.system() == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif platform.system() == "Darwin":
                subprocess.call(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
            else:
                os.system("xdg-screensaver lock 2>/dev/null || gnome-screensaver-command -l 2>/dev/null || dm-tool lock 2>/dev/null")
            return "Screen lock panniten Sir."
        except Exception as e:
            return f"Lock failed: {e}"

# Specific intent tools redirecting to windows_control logic

class ShutdownTool(WindowsControlTool):
    name = "shutdown_system"
    description = "Shutdown computer after confirmation"
    required_permission = 3
    def execute(self, args):
        return self._shutdown()

class RestartTool(WindowsControlTool):
    name = "restart_system"
    def execute(self, args):
        return self._restart()

class LockScreenTool(WindowsControlTool):
    name = "lock_screen"
    description = "Lock screen"
    dangerous = False
    required_permission = 1
    def execute(self, args):
        return self._lock()

class SleepTool(WindowsControlTool):
    name = "sleep_system"
    def execute(self, args):
        return self._sleep()
