"""
JARVIS Core - State Manager
Tracks current assistant state: listening, thinking, speaking, idle, etc.
"""
import time
import threading
from enum import Enum
from typing import Optional, Dict, Any

class AssistantState(str, Enum):
    OFFLINE = "offline"
    IDLE = "idle"
    LISTENING_WAKEWORD = "listening_wakeword"
    LISTENING_COMMAND = "listening_command"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    SPEAKING = "speaking"
    ERROR = "error"

class StateManager:
    def __init__(self):
        self._state = AssistantState.OFFLINE
        self._prev_state = AssistantState.OFFLINE
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {}
        self._last_change = time.time()
        self._listeners = []

    def set_state(self, new_state: AssistantState, data: Dict = None):
        with self._lock:
            self._prev_state = self._state
            self._state = new_state
            self._last_change = time.time()
            if data:
                self._data.update(data)
            # Notify listeners
            for cb in self._listeners:
                try:
                    cb(new_state, self._prev_state, data)
                except:
                    pass

    def get_state(self) -> AssistantState:
        with self._lock:
            return self._state

    def get_prev_state(self) -> AssistantState:
        with self._lock:
            return self._prev_state

    def is_state(self, state: AssistantState) -> bool:
        return self.get_state() == state

    def set_data(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value

    def get_data(self, key: str, default=None):
        with self._lock:
            return self._data.get(key, default)

    def get_all_data(self) -> Dict:
        with self._lock:
            return dict(self._data)

    def add_listener(self, callback):
        self._listeners.append(callback)

    def time_in_state(self) -> float:
        return time.time() - self._last_change

    def to_dict(self):
        return {
            "state": self._state.value,
            "prev_state": self._prev_state.value,
            "time_in_state": self.time_in_state(),
            "data": self.get_all_data()
        }

# Singleton
_state_manager = None

def get_state_manager() -> StateManager:
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
