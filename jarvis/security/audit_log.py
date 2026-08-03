"""
JARVIS Security - Audit Log
Logs every command, intent, result, confirmation
Offline JSONL file + SQLite
"""
import json
import datetime
from pathlib import Path
from typing import Dict, Any

from ..config import config
from ..utils import logger

class AuditLog:
    def __init__(self):
        self.log_file = config.AUDIT_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, command: str, intent: str = None, arguments: Dict = None, result: str = None, confirmed: bool = False, permission_level: int = 0, **kwargs):
        entry = {
            "time": datetime.datetime.now().isoformat(),
            "command": command,
            "intent": intent,
            "arguments": arguments,
            "result": result[:500] if result else None,
            "confirmed": confirmed,
            "permission_level": permission_level,
            "offline_only": config.OFFLINE_ONLY
        }
        entry.update(kwargs)
        
        # Append to file (JSONL)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Audit log write failed: {e}")
        
        # Also log to main logger
        logger.info(f"AUDIT: {intent} | {command} | confirmed={confirmed} | level={permission_level}")
        
        return entry
    
    def get_recent(self, limit: int = 50):
        """Get recent audit entries"""
        try:
            if not self.log_file.exists():
                return []
            lines = self.log_file.read_text(encoding='utf-8').strip().split('\n')
            entries = []
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line))
                except:
                    continue
            return entries
        except Exception as e:
            logger.error(f"Audit read failed: {e}")
            return []

# Singleton
_audit_log = None

def get_audit_log() -> AuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log
