"""
JARVIS Memory - Knowledge Base, offline local search
Uses SQLite FTS5, FAISS optional, Whoosh fallback
"""
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict

from ..config import config
from ..utils import logger
from .database import get_memory_db

class KnowledgeBase:
    def __init__(self):
        self.db = get_memory_db()
        self.db_path = config.DB_FILE

    def add_document(self, title: str, content: str, source: str = "user"):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            now = datetime.datetime.now().isoformat()
            c.execute("INSERT INTO knowledge (title, content, source, created) VALUES (?, ?, ?, ?)",
                      (title, content, source, now))
            doc_id = c.lastrowid
            
            # Try FTS
            try:
                c.execute("INSERT INTO knowledge_fts (rowid, title, content) VALUES (?, ?, ?)",
                          (doc_id, title, content))
            except Exception as e:
                logger.debug(f"FTS insert failed: {e}")
            
            conn.commit()
            conn.close()
            logger.info(f"Knowledge added: {title}")
            return doc_id
        except Exception as e:
            logger.error(f"Knowledge add failed: {e}")
            return None

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Try FTS5 search
            try:
                c.execute("SELECT k.id, k.title, k.content, k.source FROM knowledge_fts f JOIN knowledge k ON k.id = f.rowid WHERE knowledge_fts MATCH ? LIMIT ?",
                          (query, limit))
                rows = c.fetchall()
                if rows:
                    conn.close()
                    return [{"id": r[0], "title": r[1], "content": r[2][:500], "source": r[3]} for r in rows]
            except Exception as e:
                logger.debug(f"FTS search failed: {e}, fallback to LIKE")
            
            # Fallback LIKE
            c.execute("SELECT id, title, content, source FROM knowledge WHERE title LIKE ? OR content LIKE ? LIMIT ?",
                      (f"%{query}%", f"%{query}%", limit))
            rows = c.fetchall()
            conn.close()
            return [{"id": r[0], "title": r[1], "content": r[2][:500], "source": r[3]} for r in rows]
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []

    def index_folder(self, folder: Path, extensions: List[str] = None):
        """Index local folder - personal notes, docs"""
        if extensions is None:
            extensions = [".txt", ".md", ".pdf"]
        
        folder = Path(folder)
        if not folder.exists():
            logger.warning(f"Index folder not found: {folder}")
            return 0
        
        count = 0
        for ext in extensions:
            for file in folder.rglob(f"*{ext}"):
                try:
                    if file.stat().st_size > 10*1024*1024:  # Skip >10MB
                        continue
                    content = ""
                    if ext in (".txt", ".md"):
                        content = file.read_text(encoding='utf-8', errors='ignore')[:10000]
                    # PDF would need pdfminer, skip for now
                    if content:
                        self.add_document(file.name, content, str(file))
                        count += 1
                except Exception as e:
                    logger.debug(f"Index file {file} failed: {e}")
        
        logger.info(f"Indexed {count} files from {folder}")
        return count

def get_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase()
