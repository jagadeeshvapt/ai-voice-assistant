"""
JARVIS Memory - Reminders & Scheduler, offline using APScheduler + SQLite check
"""
import threading
import time
import datetime
from typing import Callable, List, Dict

from ..config import config
from ..utils import logger
from .database import get_memory_db

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

class ReminderManager:
    def __init__(self):
        self.db = get_memory_db()
        self._running = False
        self._thread = None
        self._callback: Callable = None
        self._stop_event = threading.Event()
        self._scheduler = None
        
        if APSCHEDULER_AVAILABLE:
            try:
                self._scheduler = BackgroundScheduler()
                self._scheduler.start()
                logger.info("APScheduler started for reminders")
            except Exception as e:
                logger.error(f"APScheduler start failed: {e}")
                self._scheduler = None

    def start(self, callback: Callable[[Dict], None] = None):
        self._callback = callback
        self._running = True
        self._stop_event.clear()
        
        # Start polling thread as fallback
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("Reminder manager started")

    def _poll_loop(self):
        while not self._stop_event.is_set():
            try:
                due = self.db.get_due_reminders()
                for r in due:
                    if self._callback:
                        self._callback(r)
                    self.db.mark_reminder_triggered(r)
                    logger.info(f"Reminder triggered: {r['text']}")
            except Exception as e:
                logger.error(f"Reminder poll error: {e}")
            
            # Check every N seconds
            interval = config.get_yaml_config().get("scheduler", {}).get("check_interval_seconds", 10)
            time.sleep(interval)

    def stop(self):
        self._running = False
        self._stop_event.set()
        if self._scheduler:
            try:
                self._scheduler.shutdown()
            except:
                pass
        logger.info("Reminder manager stopped")

    def add_reminder(self, text: str, remind_time: datetime.datetime) -> Dict:
        return self.db.add_reminder(text, remind_time)

    def add_timer(self, duration_seconds: int, text: str = "Timer") -> Dict:
        remind_time = datetime.datetime.now() + datetime.timedelta(seconds=duration_seconds)
        return self.add_reminder(f"{text} ({duration_seconds}s)", remind_time)

    def list_pending(self) -> List[Dict]:
        return [r for r in self.db.data.get("reminders", []) if not r.get("triggered")]

# Singleton
_reminder_manager = None

def get_reminder_manager() -> ReminderManager:
    global _reminder_manager
    if _reminder_manager is None:
        _reminder_manager = ReminderManager()
    return _reminder_manager
