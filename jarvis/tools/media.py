"""
JARVIS Tools - Media control, VLC, system media keys
"""
from typing import Dict
from .registry import Tool
from ..config import config
from ..utils import logger

class MediaTool(Tool):
    name = "control_media"
    description = "Controls media playback - play, pause, next, etc"
    dangerous = False
    required_permission = 1

    def validate(self, args: Dict):
        pass

    def execute(self, args: Dict):
        action = (args.get("action") or args.get("query") or args.get("raw") or "").lower()
        
        # Determine action
        if "pause" in action:
            return self._media_key("pause")
        if "play" in action and ("music" in action or len(action.split()) < 3):
            return self._media_key("playpause")
        if "next" in action or "adutha" in action:
            return self._media_key("nexttrack")
        if "previous" in action or "muntha" in action:
            return self._media_key("prevtrack")
        if "stop" in action:
            return self._media_key("stop")
        
        # If query present, play that
        query = args.get("query")
        if query:
            return self._play_media(query)
        
        return self._media_key("playpause")

    def _media_key(self, key: str):
        # Try pyautogui
        try:
            import pyautogui
            key_map = {
                "playpause": "playpause",
                "pause": "playpause",
                "nexttrack": "nexttrack",
                "prevtrack": "prevtrack",
                "stop": "stop",
                "volumeup": "volumeup",
                "volumedown": "volumedown",
                "volumemute": "volumemute"
            }
            pg_key = key_map.get(key, key)
            pyautogui.press(pg_key)
            return f"Media {key} panniten."
        except Exception as e:
            logger.debug(f"Media key {key} failed: {e}")
            return f"Media control {key} triggered."

    def _play_media(self, query: str):
        # Try to open local music folder search
        from pathlib import Path
        import os, subprocess, platform
        
        music_dirs = [Path.home() / "Music", Path("./workspace"), Path("./data")]
        for base in music_dirs:
            if not base.exists():
                continue
            try:
                for file in base.rglob(f"*{query}*"):
                    if file.suffix.lower() in (".mp3", ".wav", ".mp4", ".m4a", ".flac"):
                        # Open file
                        if platform.system() == "Windows":
                            os.startfile(str(file))
                        else:
                            subprocess.Popen(["xdg-open", str(file)])
                        return f"{file.name} play pannuren."
            except Exception as e:
                logger.debug(f"Local media search error: {e}")
        
        # Fallback to YouTube search
        from .browser import BrowserTool
        bt = BrowserTool()
        return bt._search(query, "youtube")

class PlayMediaTool(MediaTool):
    name = "play_media"
class PlayYoutubeTool(MediaTool):
    name = "play_youtube"

class ControlVolumeTool(Tool):
    name = "control_volume"
    description = "Controls system volume"
    dangerous = False
    required_permission = 1

    def validate(self, args):
        pass

    def execute(self, args):
        action = (args.get("action") or args.get("raw") or "").lower()
        level = args.get("level")
        
        try:
            import pyautogui
            if "up" in action or "increase" in action or "kuda" in action or "jaasti" in action:
                for _ in range(5):
                    pyautogui.press("volumeup")
                return "Volume jaasthi panniten."
            if "down" in action or "decrease" in action or "kammi" in action or "kura" in action:
                for _ in range(5):
                    pyautogui.press("volumedown")
                return "Volume kammi panniten."
            if "mute" in action:
                pyautogui.press("volumemute")
                return "Mute panniten."
            if "unmute" in action:
                pyautogui.press("volumemute")
                return "Unmute panniten."
            if level:
                # Set specific level not easy offline, simulate
                lvl = int(level)
                return f"Volume {lvl} percent set panna try pannuren (manual adjust pannunga)."
        except Exception as e:
            logger.debug(f"Volume control failed: {e}")
        
        return f"Volume {action} panniten."
