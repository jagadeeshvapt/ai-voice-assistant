"""
JARVIS UI - Notifications, local desktop notifications
"""
import platform
from typing import Optional

from ..config import config
from ..utils import logger

class NotificationManager:
    def __init__(self):
        self.quiet_hours = config.get_yaml_config().get("ui", {}).get("quiet_hours", {})
    
    def is_quiet_hours(self) -> bool:
        try:
            import datetime
            now = datetime.datetime.now().time()
            start_str = self.quiet_hours.get("start", "22:00")
            end_str = self.quiet_hours.get("end", "07:00")
            start = datetime.datetime.strptime(start_str, "%H:%M").time()
            end = datetime.datetime.strptime(end_str, "%H:%M").time()
            
            if start <= end:
                return start <= now <= end
            else:
                # Overnight
                return now >= start or now <= end
        except:
            return False

    def notify(self, title: str, message: str, silent: bool = False):
        if self.is_quiet_hours() and not silent:
            logger.info(f"Quiet hours - notification suppressed: {title}")
            return
        
        # Try plyer, win10toast, or fallback to print
        try:
            if platform.system() == "Windows":
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5, threaded=True)
                    return
                except:
                    pass
            
            try:
                from plyer import notification
                notification.notify(title=title, message=message, app_name="JARVIS", timeout=5)
                return
            except:
                pass
        except Exception as e:
            logger.debug(f"Desktop notification failed: {e}")
        
        # Fallback
        print(f"\n[NOTIFICATION] {title}: {message}\n")

# Singleton
_notif_manager = None

def get_notification_manager() -> NotificationManager:
    global _notif_manager
    if _notif_manager is None:
        _notif_manager = NotificationManager()
    return _notif_manager
