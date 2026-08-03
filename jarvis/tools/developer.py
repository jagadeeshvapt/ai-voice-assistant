"""
JARVIS Tools - Developer assistant, safe project creation, code generation
"""
import os
from pathlib import Path
from typing import Dict
from .registry import Tool
from ..config import config
from ..utils import logger

class DeveloperTool(Tool):
    name = "developer"
    description = "Developer tools - create projects, write code, etc"
    dangerous = False
    required_permission = 1

    def validate(self, args):
        pass

    def execute(self, args):
        raw = (args.get("raw") or "").lower()
        if "create" in raw and "project" in raw:
            return self._create_project(args)
        if "code" in raw or "python" in raw:
            return self._generate_code(args)
        return "Developer tool - say 'create python project' or 'write code for sorting'"

    def _create_project(self, args: Dict):
        ptype = args.get("type") or args.get("query") or "python"
        raw = args.get("raw") or ""
        
        # Extract project name
        import re
        m = re.search(r"project (?:named )?(\w+)", raw.lower())
        name = m.group(1) if m else "my_project"
        
        base = Path("./workspace") / name
        base.mkdir(parents=True, exist_ok=True)
        
        if "python" in ptype.lower() or "python" in raw.lower():
            # Create basic python project
            (base / "main.py").write_text('# Created by JARVIS\nprint("Hello from JARVIS project")\n', encoding='utf-8')
            (base / "requirements.txt").write_text("# Dependencies\n", encoding='utf-8')
            (base / "README.md").write_text(f"# {name}\nCreated by JARVIS Local Assistant\n", encoding='utf-8')
            (base / ".gitignore").write_text("__pycache__/\nvenv/\n.env\n", encoding='utf-8')
            return f"Python project {name} create panniten at {base}. VS Code la open pannalama?"
        
        return f"Project {name} create panniten at {base}"

    def _generate_code(self, args: Dict):
        query = args.get("query") or args.get("raw") or ""
        # Simple local code generation without LLM (templates)
        if "sort" in query.lower():
            code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# Example
print(bubble_sort([5,2,9,1]))
"""
            # Save to file
            Path("./workspace/snippets").mkdir(parents=True, exist_ok=True)
            Path("./workspace/snippets/sort.py").write_text(code, encoding='utf-8')
            return f"Sorting code generate panniten, saved to workspace/snippets/sort.py:\n{code[:400]}"
        
        return f"Code generation for '{query}' - offline template illa, but example create pannalam. Enna code venum-nu detail-a sollunga."

class CreateProjectTool(DeveloperTool):
    name = "create_project"
