"""
JARVIS Memory - SQLite Database, strict offline
Stores conversations, preferences, audit logs, knowledge base index
"""
import sqlite3
import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional

from ..config import config
from ..utils import logger

class MemoryDatabase:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DB_FILE
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
        # Also keep JSON memory for backward compat
        self.json_path = config.MEMORY_FILE
        self._json_data = {
            "user_name": "Sir",
            "preferences": {},
            "history": [],
            "todo": [],
            "reminders": [],
            "learned_facts": {},
            "created_at": datetime.datetime.now().isoformat()
        }
        self._load_json()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Conversations
            c.execute('''CREATE TABLE IF NOT EXISTS conversations
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp TEXT,
                          user_input TEXT,
                          intent TEXT,
                          assistant_response TEXT,
                          tool_result TEXT)''')
            
            # Preferences
            c.execute('''CREATE TABLE IF NOT EXISTS preferences
                         (key TEXT PRIMARY KEY,
                          value TEXT,
                          updated TEXT)''')
            
            # Reminders (duplicate of JSON but for querying)
            c.execute('''CREATE TABLE IF NOT EXISTS reminders
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          text TEXT,
                          remind_time TEXT,
                          created TEXT,
                          triggered INTEGER DEFAULT 0)''')
            
            # Knowledge base FTS5
            c.execute('''CREATE TABLE IF NOT EXISTS knowledge
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT,
                          content TEXT,
                          source TEXT,
                          created TEXT)''')
            # Try FTS5 virtual table
            try:
                c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(title, content, content='knowledge', content_rowid='id')''')
            except Exception as e:
                logger.debug(f"FTS5 not available: {e}")
            
            # Audit (mirror)
            c.execute('''CREATE TABLE IF NOT EXISTS audit
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp TEXT,
                          command TEXT,
                          intent TEXT,
                          result TEXT,
                          confirmed INTEGER)''')
            
            conn.commit()
            conn.close()
            logger.info(f"SQLite DB initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"DB init failed: {e}")

    def _load_json(self):
        try:
            if self.json_path.exists():
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._json_data.update(data)
        except Exception as e:
            logger.error(f"JSON memory load failed: {e}")

    def _save_json(self):
        try:
            # Keep last 200 history
            if len(self._json_data.get("history", [])) > config.MAX_HISTORY:
                self._json_data["history"] = self._json_data["history"][-config.MAX_HISTORY:]
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self._json_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"JSON save failed: {e}")

    # User name handling
    def get_user_name(self) -> str:
        return self._json_data.get("user_name", "Sir")

    def set_user_name(self, name: str):
        self._json_data["user_name"] = name
        self._save_json()
        self.set_preference("user_name", name)

    def set_preference(self, key: str, value: str):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO preferences (key, value, updated) VALUES (?, ?, ?)",
                      (key, value, datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Set pref failed: {e}")
        self._json_data.setdefault("preferences", {})[key] = value
        self._save_json()

    def get_preference(self, key: str, default=None):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT value FROM preferences WHERE key=?", (key,))
            row = c.fetchone()
            conn.close()
            if row:
                return row[0]
        except:
            pass
        return self._json_data.get("preferences", {}).get(key, default)

    # Conversations
    def add_conversation(self, user_input: str, intent_data_or_response, tool_result=None):
        """Backward compat: support old signature (user_input, assistant_response) and new (user_input, intent_data, tool_result)"""
        timestamp = datetime.datetime.now().isoformat()
        
        if isinstance(intent_data_or_response, dict):
            # New style: intent_data dict, tool_result
            intent = intent_data_or_response.get("intent", "")
            response = intent_data_or_response.get("reply", "") or str(tool_result)[:500]
            # Save to JSON history for backward compat
            self._json_data.setdefault("history", []).append({
                "timestamp": timestamp,
                "user": user_input,
                "jarvis": response,
                "intent": intent
            })
        else:
            # Old style: assistant_response string
            response = str(intent_data_or_response)
            intent = "unknown"
            self._json_data.setdefault("history", []).append({
                "timestamp": timestamp,
                "user": user_input,
                "jarvis": response
            })
        
        self._save_json()
        
        # Save to SQLite
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO conversations (timestamp, user_input, intent, assistant_response, tool_result) VALUES (?, ?, ?, ?, ?)",
                      (timestamp, user_input, intent, response, str(tool_result)[:1000] if tool_result else ""))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB conversation save failed: {e}")

    def get_history(self, limit: int = 10) -> List[Dict]:
        return self._json_data.get("history", [])[-limit:]

    def get_context_for_llm(self, limit: int = 6) -> str:
        hist = self.get_history(limit)
        if not hist:
            return ""
        lines = []
        for h in hist:
            lines.append(f"User: {h.get('user','')}")
            lines.append(f"JARVIS: {h.get('jarvis','')}")
        return "\n".join(lines)

    def search_memory(self, query: str) -> List[Dict]:
        q = query.lower()
        results = []
        for h in self._json_data.get("history", []):
            if q in h.get("user","").lower() or q in h.get("jarvis","").lower():
                results.append(h)
        return results[-10:]

    # Todo (backward compat with old Memory class)
    def add_todo(self, task: str):
        todo = {
            "task": task,
            "created": datetime.datetime.now().isoformat(),
            "done": False
        }
        self._json_data.setdefault("todo", []).append(todo)
        self._save_json()
        return todo

    def list_todo(self) -> List[Dict]:
        return [t for t in self._json_data.get("todo", []) if not t.get("done")]

    def complete_todo(self, index: int) -> bool:
        todos = self._json_data.get("todo", [])
        pending = [i for i, t in enumerate(todos) if not t.get("done")]
        if 0 <= index < len(pending):
            real_idx = pending[index]
            todos[real_idx]["done"] = True
            todos[real_idx]["completed_at"] = datetime.datetime.now().isoformat()
            self._save_json()
            return True
        return False

    # Reminders - delegate to JSON but keep compatibility
    def add_reminder(self, text: str, remind_time):
        import datetime as dt
        if isinstance(remind_time, str):
            rt_iso = remind_time
        else:
            rt_iso = remind_time.isoformat() if hasattr(remind_time, 'isoformat') else str(remind_time)
        
        reminder = {
            "text": text,
            "time": rt_iso,
            "created": dt.datetime.now().isoformat(),
            "triggered": False
        }
        self._json_data.setdefault("reminders", []).append(reminder)
        self._save_json()
        
        # Also SQLite
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO reminders (text, remind_time, created, triggered) VALUES (?, ?, ?, 0)",
                      (text, rt_iso, dt.datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Reminder DB save failed: {e}")
        
        return reminder

    def get_due_reminders(self):
        # Use JSON list for simplicity
        import datetime as dt
        now = dt.datetime.now()
        due = []
        for r in self._json_data.get("reminders", []):
            if not r.get("triggered"):
                try:
                    rt = dt.datetime.fromisoformat(r["time"])
                    if rt <= now:
                        due.append(r)
                except:
                    continue
        return due

    def mark_reminder_triggered(self, reminder: Dict):
        reminder["triggered"] = True
        self._save_json()

    def learn_fact(self, key: str, value: str):
        self._json_data.setdefault("learned_facts", {})[key] = value
        self._save_json()

    @property
    def data(self):
        return self._json_data

# Singleton
_db_instance = None

def get_memory_db() -> MemoryDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = MemoryDatabase()
    return _db_instance

# Backward compat alias
def get_memory():
    return get_memory_db()
