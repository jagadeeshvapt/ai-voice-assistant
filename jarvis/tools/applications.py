"""
JARVIS Tools - Application Control, Windows focus, strict offline
"""
import os
import platform
import subprocess
from typing import Dict
from .registry import Tool
from ..utils import logger
from ..config import config

class ApplicationsTool(Tool):
    name = "open_application"
    description = "Opens, closes, lists applications"
    dangerous = False
    required_permission = 1
    
    def __init__(self):
        # Map common apps
        self.app_map = {
            "notepad": "notepad" if platform.system() == "Windows" else "gedit",
            "calculator": "calc" if platform.system() == "Windows" else "gnome-calculator",
            "chrome": "chrome",
            "google chrome": "chrome",
            "browser": "chrome",
            "firefox": "firefox",
            "edge": "msedge",
            "vscode": "code",
            "code": "code",
            "visual studio code": "code",
            "explorer": "explorer",
            "files": "explorer" if platform.system() == "Windows" else "nautilus",
            "file explorer": "explorer",
            "terminal": "cmd" if platform.system() == "Windows" else "gnome-terminal",
            "cmd": "cmd",
            "command prompt": "cmd",
            "spotify": "spotify",
            "vlc": "vlc",
            "word": "winword",
            "excel": "excel",
            "paint": "mspaint",
            "task manager": "taskmgr",
        }

    def validate(self, arguments: Dict):
        app = arguments.get("application") or arguments.get("app") or arguments.get("name")
        if not app and arguments.get("intent") not in ("list_applications",):
            raise ValueError("Application name required")

    def execute(self, arguments: Dict):
        intent = arguments.get("_intent") or self.name
        
        # Handle different intents that route to this tool
        # The registry may call this for close_application etc - we handle via intent arg
        action = arguments.get("action", "open")
        app_name = (arguments.get("application") or arguments.get("app") or arguments.get("name") or "").lower().strip()
        
        # If called for close_application
        if "close" in arguments.get("raw", "").lower() or action == "close":
            return self._close_app(app_name)
        
        if app_name in ("list", "all", "running"):
            return self._list_running()
        
        return self._open_app(app_name, arguments.get("raw", ""))

    def _open_app(self, app_name: str, raw: str = ""):
        if not app_name:
            return "Entha application open pannanum-nu sollunga."
        
        # Normalize app name
        app_name_clean = app_name.lower().strip()
        # Remove filler like "application", "app"
        app_name_clean = app_name_clean.replace(" application", "").replace(" app", "").strip()
        
        cmd = self.app_map.get(app_name_clean, app_name_clean)
        
        # Handle multi-word like "my project folder"
        # If path exists, open it
        from pathlib import Path
        possible_path = Path(app_name)
        if possible_path.exists():
            try:
                if platform.system() == "Windows":
                    os.startfile(str(possible_path))
                else:
                    subprocess.Popen(["xdg-open", str(possible_path)])
                return f"{app_name} open panniten."
            except Exception as e:
                logger.error(f"Open path failed: {e}")
        
        try:
            if platform.system() == "Windows":
                # Try start command
                # Use os.system for simplicity, avoid blocking
                os.system(f'start "" "{cmd}"' if " " in cmd else f"start {cmd}")
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-a", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return f"{app_name.title()} open panniten." if config.LANGUAGE == "tanglish" else f"Opened {app_name}."
        except Exception as e:
            logger.error(f"Open app {app_name} failed: {e}")
            return f"{app_name} open panna mudiyala: {e}"

    def _close_app(self, app_name: str):
        try:
            if platform.system() == "Windows":
                # Use taskkill
                os.system(f'taskkill /IM {app_name}.exe /F 2>nul || taskkill /IM {app_name} /F 2>nul')
            else:
                os.system(f"pkill {app_name} 2>/dev/null")
            return f"{app_name} close panniten."
        except Exception as e:
            return f"Close failed: {e}"

    def _list_running(self):
        try:
            import psutil
            procs = [p.info['name'] for p in psutil.process_iter(['name'])]
            unique = list(set(procs))[:20]
            return f"Running apps: {', '.join(unique)}"
        except:
            return "Running apps list not available"

# Additional tool aliases for same class
class CloseApplicationTool(ApplicationsTool):
    name = "close_application"
    description = "Closes applications"

class ListApplicationsTool(ApplicationsTool):
    name = "list_applications"
    description = "Lists running applications"
