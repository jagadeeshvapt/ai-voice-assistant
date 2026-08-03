"""
JARVIS Security - Permission Manager
Levels:
0 - Read-only (time, status, search, read file)
1 - Safe action (open app, volume, screenshot, create note)
2 - Confirmation required (delete, move, install, close all, send)
3 - PIN required (shutdown, admin, door lock, format, etc)
"""
from typing import Dict
from ..config import config
from ..core.errors import ConfirmationRequired, PinRequired, SecurityViolation

class PermissionManager:
    def __init__(self):
        self.level_names = {
            0: "READ_ONLY",
            1: "SAFE_ACTION",
            2: "CONFIRMATION_REQUIRED",
            3: "PIN_REQUIRED"
        }
        
        # Map intents to levels (as per spec)
        self.intent_levels = {
            # Level 0
            "get_time": 0,
            "get_date": 0,
            "system_status": 0,
            "search_files": 0,
            "knowledge_query": 0,
            "read_file": 0,
            "list_folders": 0,
            
            # Level 1
            "open_application": 1,
            "open_website": 1,
            "browser_search": 1,
            "play_youtube": 1,
            "play_media": 1,
            "control_media": 1,
            "control_volume": 1,
            "take_screenshot": 1,
            "create_file": 1,
            "create_folder": 1,
            "create_note": 1,
            "set_reminder": 1,
            "set_timer": 1,
            "lock_screen": 1,
            
            # Level 2
            "close_application": 2,
            "close_all_apps": 2,
            "file_operation": 2,
            "move_file": 2,
            "delete_file": 2,
            "send_message": 2,
            "send_email": 2,
            "install_software": 2,
            "sleep_system": 2,
            
            # Level 3
            "shutdown_system": 3,
            "restart_system": 3,
            "format_disk": 3,
            "admin_command": 3,
            "change_security": 3,
            "door_lock": 3,
            "door_unlock": 3,
        }
        
        # Override from config if provided
        yaml_perms = config.get_yaml_config().get("permissions", {})
        # Not handling override in detail for now

    def get_level(self, intent_data: Dict) -> int:
        intent = intent_data.get("intent", "")
        # Explicit level from intent
        if "permission_level" in intent_data:
            return intent_data["permission_level"]
        return self.intent_levels.get(intent, 1)

    def check_permission(self, intent_data: Dict):
        """
        Check if intent is allowed, raises ConfirmationRequired or PinRequired if needed
        Returns True if allowed immediately, else raises
        """
        level = self.get_level(intent_data)
        intent = intent_data.get("intent", "")
        
        # Check blocked folders for file operations
        if intent in ("delete_file", "file_operation", "create_file", "create_folder"):
            args = intent_data.get("arguments", {})
            target = args.get("target") or args.get("name") or args.get("path") or ""
            if self._is_blocked_path(target):
                raise SecurityViolation(f"Path {target} is blocked for security")
        
        if level == 0 or level == 1:
            # Always allowed
            return True
        
        if level == 2:
            if intent_data.get("confirmed") or config.DEBUG:
                return True
            # Check config if confirmation disabled
            if not config.REQUIRE_CONFIRM_DELETE and intent in ("delete_file", "file_operation"):
                return True
            raise ConfirmationRequired(
                f"{intent} requires confirmation. Shall I proceed? Say yes.",
                intent_data=intent_data
            )
        
        if level == 3:
            if intent_data.get("pin_verified"):
                return True
            if intent_data.get("confirmed") and not config.REQUIRE_PIN_ADMIN:
                return True
            if config.REQUIRE_PIN_ADMIN:
                raise PinRequired(
                    f"{intent} is a critical action and requires PIN verification.",
                    intent_data=intent_data
                )
            else:
                raise ConfirmationRequired(
                    f"{intent} is critical and requires confirmation. Confirm?",
                    intent_data=intent_data
                )

    def mark_confirmed(self, intent_data: Dict):
        intent_data["confirmed"] = True
        return intent_data

    def mark_pin_verified(self, intent_data: Dict):
        intent_data["pin_verified"] = True
        intent_data["confirmed"] = True
        return intent_data

    def _is_blocked_path(self, path_str: str) -> bool:
        if not path_str:
            return False
        from pathlib import Path
        try:
            path = Path(path_str).resolve() if Path(path_str).is_absolute() else (config.BASE_DIR / path_str).resolve()
            for blocked in config.BLOCKED_FOLDERS:
                try:
                    if blocked and str(blocked) in str(path):
                        return True
                    # Check if path is inside blocked
                    if blocked.exists() and blocked.resolve() in path.parents:
                        return True
                except:
                    continue
        except:
            pass
        return False

# Singleton
_perm_manager = None

def get_permission_manager() -> PermissionManager:
    global _perm_manager
    if _perm_manager is None:
        _perm_manager = PermissionManager()
    return _perm_manager
