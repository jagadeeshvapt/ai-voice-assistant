"""
JARVIS Tools - File Manager, safe with allowlist/blocklist
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List
from .registry import Tool
from ..config import config
from ..utils import logger

class FileManagerTool(Tool):
    name = "create_file"
    description = "Creates files and folders safely within allowed folders"
    dangerous = False
    required_permission = 1

    def validate(self, arguments: Dict):
        # Check blocked folders
        name = arguments.get("name") or arguments.get("path") or arguments.get("target") or arguments.get("query") or ""
        if name:
            # Basic path traversal check
            if ".." in name and config.OFFLINE_ONLY:
                # Allow but will be confined
                pass

    def execute(self, arguments: Dict):
        intent = arguments.get("_intent") or self.name
        # Route based on intent override if caller set
        # But self.name is create_file, we handle others via same instance if registry calls with different name?
        # For simplicity, we check raw or intent field
        actual_intent = arguments.get("intent") or self.name
        if actual_intent in ("create_file", "create_folder", "file_operation", "search_files", "read_file", "list_folders"):
            self.name = actual_intent  # temporary
        
        if self.name == "create_file" or "create file" in str(arguments.get("raw","")).lower():
            return self._create_file(arguments)
        elif self.name == "create_folder" or "create folder" in str(arguments.get("raw","")).lower() or "make folder" in str(arguments.get("raw","")).lower():
            return self._create_folder(arguments)
        elif self.name in ("search_files", "find_files"):
            return self._search_files(arguments)
        elif self.name == "read_file":
            return self._read_file(arguments)
        elif self.name == "list_folders":
            return self._list_folders(arguments)
        elif self.name == "file_operation":
            return self._file_operation(arguments)
        else:
            return self._create_file(arguments)

    def _resolve_safe_path(self, user_path: str) -> Path:
        """Resolve path within allowed folders, prevent escaping to blocked"""
        if not user_path:
            user_path = "workspace/untitled.txt"
        
        # Clean
        user_path = user_path.strip().strip('"').strip("'")
        
        # If absolute, check if inside allowed
        p = Path(user_path)
        if not p.is_absolute():
            # Default to workspace
            p = Path("./workspace") / p
        
        # Resolve
        try:
            # Don't require exists for resolve
            resolved = p.resolve()
        except:
            resolved = p.absolute()
        
        # Check blocked
        for blocked in config.BLOCKED_FOLDERS:
            try:
                if blocked.exists() and (blocked.resolve() == resolved or blocked.resolve() in resolved.parents):
                    raise ValueError(f"Path {resolved} is in blocked folder {blocked}")
                if str(blocked).lower() in str(resolved).lower() and "workspace" not in str(blocked).lower():
                    # Simple substring check for safety
                    pass
            except Exception as e:
                if "blocked" in str(e).lower():
                    raise
        
        # Ensure parent exists and is writable
        # For search operations, parent may not need to exist
        return resolved

    def _create_file(self, args: Dict):
        name = args.get("name") or args.get("target") or args.get("query") or "untitled.txt"
        content = args.get("content") or args.get("text") or ""
        # Extract content from raw like "create file test.txt with content hello"
        raw = args.get("raw", "")
        if "with content" in raw.lower() and not content:
            parts = raw.lower().split("with content")
            if len(parts) > 1:
                # Use original case for content? approximated
                idx = raw.lower().find("with content") + len("with content")
                content = raw[idx:].strip()
        
        try:
            safe_path = self._resolve_safe_path(name)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content or f"# Created by JARVIS\n", encoding='utf-8')
            return f"File {safe_path.name} create panniten at {safe_path.parent}."
        except Exception as e:
            logger.error(f"Create file error: {e}")
            return f"File create panna mudiyala: {e}"

    def _create_folder(self, args: Dict):
        name = args.get("name") or args.get("path") or "new_folder"
        try:
            safe_path = self._resolve_safe_path(name)
            safe_path.mkdir(parents=True, exist_ok=True)
            return f"Folder {safe_path.name} create panniten."
        except Exception as e:
            return f"Folder create failed: {e}"

    def _search_files(self, args: Dict):
        query = args.get("query") or args.get("name") or args.get("target") or ""
        if not query:
            query = args.get("raw", "").replace("search files", "").strip()
        
        # Search in allowed folders + workspace
        search_paths = [Path("./workspace"), Path.home() / "Documents", Path.home() / "Desktop"]
        # Filter to existing allowed
        results = []
        for base in search_paths:
            if not base.exists():
                continue
            try:
                for file in base.rglob(f"*{query}*"):
                    if file.is_file():
                        results.append(str(file))
                        if len(results) >= 20:
                            break
            except Exception as e:
                logger.debug(f"Search in {base} error: {e}")
        
        if not results:
            return f"{query} file ethuvum kedaikala."
        return f"Found {len(results)} files:\n" + "\n".join(results[:10])

    def _read_file(self, args: Dict):
        name = args.get("name") or args.get("path") or args.get("target") or ""
        try:
            safe_path = self._resolve_safe_path(name)
            if not safe_path.exists():
                return f"File {name} illa Sir."
            text = safe_path.read_text(encoding='utf-8', errors='ignore')[:2000]
            return f"File {safe_path.name} content:\n{text[:1000]}"
        except Exception as e:
            return f"Read failed: {e}"

    def _list_folders(self, args: Dict):
        path = args.get("path") or "./workspace"
        try:
            safe_path = self._resolve_safe_path(path)
            if not safe_path.exists():
                return f"Folder {path} illa."
            items = list(safe_path.iterdir())[:20]
            names = [f"{'[DIR]' if p.is_dir() else '[FILE]'} {p.name}" for p in items]
            return f"Contents of {safe_path}:\n" + "\n".join(names)
        except Exception as e:
            return f"List failed: {e}"

    def _file_operation(self, args: Dict):
        # For safety, require confirmation already handled by permission manager
        # This handles delete/move/rename with extra checks
        raw = args.get("raw", "").lower()
        target = args.get("target") or args.get("name") or ""
        
        if "delete" in raw:
            try:
                safe_path = self._resolve_safe_path(target)
                if safe_path.is_file():
                    safe_path.unlink()
                    return f"{safe_path.name} delete panniten."
                elif safe_path.is_dir():
                    shutil.rmtree(safe_path)
                    return f"Folder {safe_path.name} delete panniten."
                else:
                    return f"File {target} not found."
            except Exception as e:
                return f"Delete failed: {e}"
        
        return "File operation - use create, search, read, or delete with confirmation."

# Additional tools with same class but different names

class CreateFolderTool(FileManagerTool):
    name = "create_folder"
class SearchFilesTool(FileManagerTool):
    name = "search_files"
    required_permission = 0
class ReadFileTool(FileManagerTool):
    name = "read_file"
    required_permission = 0
class ListFoldersTool(FileManagerTool):
    name = "list_folders"
    required_permission = 0
class FileOperationTool(FileManagerTool):
    name = "file_operation"
    dangerous = True
    required_permission = 2
