"""
JARVIS Core - Event Bus (pub/sub for decoupled modules)
Strict offline, in-memory event bus
"""
import threading
import queue
import time
from typing import Callable, Dict, List, Any
from ..utils import logger

class Event:
    def __init__(self, type: str, data: Dict[str, Any] = None, source: str = "system"):
        self.type = type
        self.data = data or {}
        self.source = source
        self.timestamp = time.time()

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._event_queue = queue.Queue()
        self._running = False
        self._thread = None

    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            if logger:
                logger.debug(f"Subscribed to {event_type}: {callback.__name__}")

    def unsubscribe(self, event_type: str, callback: Callable):
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [c for c in self._subscribers[event_type] if c != callback]

    def publish(self, event: Event):
        self._event_queue.put(event)
        # Also try immediate dispatch for sync subscribers
        self._dispatch(event)

    def publish_sync(self, event_type: str, data: Dict = None, source: str = "system"):
        evt = Event(event_type, data, source)
        self._dispatch(evt)

    def _dispatch(self, event: Event):
        with self._lock:
            callbacks = self._subscribers.get(event.type, []) + self._subscribers.get("*", [])
        for cb in callbacks:
            try:
                cb(event)
            except Exception as e:
                if logger:
                    logger.error(f"EventBus callback error for {event.type}: {e}")

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            try:
                event = self._event_queue.get(timeout=0.5)
                self._dispatch(event)
            except queue.Empty:
                continue
            except Exception as e:
                if logger:
                    logger.error(f"EventBus loop error: {e}")

    def stop(self):
        self._running = False

# Singleton
_event_bus = None

def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        _event_bus.start()
    return _event_bus
