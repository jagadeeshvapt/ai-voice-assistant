"""
JARVIS Security - Confirmation Manager
Handles yes/no confirmations for dangerous actions
"""
import uuid
import time
from typing import Dict, Optional

class ConfirmationManager:
    def __init__(self):
        self._pending: Dict[str, Dict] = {}
    
    def create_confirmation(self, intent_data: Dict) -> str:
        cid = str(uuid.uuid4())[:8]
        self._pending[cid] = {
            "intent_data": intent_data,
            "created": time.time(),
            "expires": time.time() + 60  # 60 sec expiry
        }
        return cid
    
    def get_pending(self, cid: str) -> Optional[Dict]:
        data = self._pending.get(cid)
        if not data:
            return None
        if time.time() > data["expires"]:
            del self._pending[cid]
            return None
        return data
    
    def is_confirmation(self, text: str) -> bool:
        """Check if user text is a confirmation"""
        text = text.lower().strip()
        yes_words = [
            "yes", "yeah", "confirm", "proceed", "do it", "go ahead",
            "aama", "sari", "seri", "pannu", "pannidu", "pannunga", "okay", "ok",
            "haan", "correct", "right"
        ]
        # Must be short (yes alone, not sentence)
        if len(text.split()) <= 3:
            for w in yes_words:
                if w in text:
                    return True
        # Explicit phrases
        if text in ("yes", "aama", "sari", "seri", "okay"):
            return True
        return False

    def is_denial(self, text: str) -> bool:
        text = text.lower().strip()
        no_words = ["no", "cancel", "stop", "abort", "illa", "venda", "vendam", "nope", "never mind"]
        if len(text.split()) <= 3:
            for w in no_words:
                if w in text:
                    return True
        if text in ("no", "illa", "venda", "cancel"):
            return True
        return False

    def clear_expired(self):
        now = time.time()
        expired = [k for k, v in self._pending.items() if v["expires"] < now]
        for k in expired:
            del self._pending[k]

# Singleton
_conf_manager = None

def get_confirmation_manager() -> ConfirmationManager:
    global _conf_manager
    if _conf_manager is None:
        _conf_manager = ConfirmationManager()
    return _conf_manager
