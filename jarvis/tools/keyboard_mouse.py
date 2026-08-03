"""
JARVIS Tools - Keyboard Mouse Control, safe
"""
from typing import Dict
from .registry import Tool
from ..utils import logger

class KeyboardMouseTool(Tool):
    name = "keyboard_mouse"
    description = "Controls keyboard and mouse"
    dangerous = False
    required_permission = 1

    def validate(self, args):
        pass

    def execute(self, args):
        action = (args.get("action") or args.get("raw") or "").lower()
        
        try:
            import pyautogui
            if "move" in action:
                # Extract coordinates?
                import re
                m = re.search(r"(\d+)\s*[,\s]\s*(\d+)", action)
                if m:
                    x, y = int(m.group(1)), int(m.group(2))
                    pyautogui.moveTo(x, y)
                    return f"Mouse {x},{y} ku move panniten."
                return "Mouse move panna coordinates sollunga."
            
            if "click" in action:
                if "right" in action:
                    pyautogui.rightClick()
                    return "Right click panniten."
                if "double" in action:
                    pyautogui.doubleClick()
                    return "Double click panniten."
                pyautogui.click()
                return "Click panniten."
            
            if "type" in action:
                text = args.get("text") or args.get("query") or ""
                if text:
                    pyautogui.typewrite(text)
                    return f"Typed: {text}"
                return "Enna type pannanum-nu sollunga."
            
            if "hotkey" in action or "shortcut" in action:
                # Example: hotkey ctrl+c
                keys = args.get("keys") or []
                if keys:
                    pyautogui.hotkey(*keys)
                    return f"Hotkey {'+'.join(keys)} press panniten."
                
        except Exception as e:
            logger.error(f"Keyboard mouse error: {e}")
            return f"Keyboard/mouse control failed: {e}"
        
        return "Keyboard/mouse - specify move, click, type, or hotkey."

class TypeTextTool(KeyboardMouseTool):
    name = "type_text"
class MoveMouseTool(KeyboardMouseTool):
    name = "move_mouse"
