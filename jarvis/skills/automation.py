import re
import os
import datetime
import json
from pathlib import Path

from .base import Skill, register_skill
from ..config import config
from ..utils import logger

@register_skill
class AutomationSkill(Skill):
    name = "automation"
    description = "Todo, reminders, notes, calculations, file creation"
    keywords = [
        "reminder", "remind me", "todo", "task", "add task", "note", "remember", "calculate",
        "what is", "plus", "minus", "multiply", "divide", "math", "solve", "create file", "write file",
        "new file", "make a file", "alarm", "timer"
    ]
    patterns = [
        r"remind me (?:to )?(.+)",
        r"set (?:a )?reminder (?:for )?(.+)",
        r"add (?:a )?todo (.+)",
        r"add task (.+)",
        r"create (?:a )?file (.+)",
        r"write (?:a )?file (.+)",
        r"calculate (.+)",
        r"what is (.+) (plus|minus|times|multiply|divide|\+|-|\*|/) (.+)",
        r"(.+) (plus|minus|times|multiply|divide) (.+)",
        r"note (?:that )?(.+)",
        r"remember (?:that )?(.+)",
    ]

    def handle(self, text, context=None):
        low = text.lower()
        from ..memory import get_memory
        memory = get_memory()

        # Calculations
        calc_result = self._try_calculate(text)
        if calc_result:
            return calc_result

        # Todo
        if any(x in low for x in ["add todo", "add task", "todo", "task list", "show todo", "list todo"]):
            if "list" in low or "show" in low or "what" in low:
                todos = memory.list_todo()
                if not todos:
                    return "Your todo list is empty, sir"
                tasks = "\n".join([f"{i+1}. {t['task']}" for i, t in enumerate(todos)])
                return f"Here are your pending tasks, sir:\n{tasks}"
            
            # Add todo
            m = re.search(r"add (?:a )?todo (.+)", low)
            if not m:
                m = re.search(r"add task (.+)", low)
            if not m:
                # Generic "todo X"
                m = re.search(r"todo (.+)", low)
            
            if m:
                task = m.group(1).strip()
                # Original casing from input
                original_task = self._extract_original(text, task)
                memory.add_todo(original_task)
                return f"Added to todo: {original_task}"
            
            # If user says "add todo" without extraction, maybe whole after keyword
            if "todo" in low:
                # ask? we do fallback
                return "What task should I add to todo?"

        if "complete todo" in low or "done todo" in low or "finish task" in low:
            m = re.search(r"(?:complete|done|finish) (?:todo|task) (\d+)", low)
            if m:
                idx = int(m.group(1)) - 1
                if memory.complete_todo(idx):
                    return f"Marked todo {idx+1} as done, sir"
                else:
                    return "Invalid todo number"

        # Reminders
        if "remind" in low or "reminder" in low:
            if "list" in low or "show" in low:
                # Show reminders
                from ..memory import get_memory
                reminders = get_memory().data.get("reminders", [])
                pending = [r for r in reminders if not r.get("triggered")]
                if not pending:
                    return "No pending reminders"
                lines = []
                for i, r in enumerate(pending):
                    lines.append(f"{i+1}. {r['text']} at {r['time']}")
                return "\n".join(lines)

            # Parse "remind me to X at Y" or "remind me to X in 5 minutes"
            m = re.search(r"remind me (?:to )?(.+)", low)
            if m:
                raw = m.group(1)
                # Try parse time
                remind_text, remind_time = self._parse_reminder(raw)
                if remind_time:
                    # Use original casing for text
                    original = self._extract_original(text, remind_text)
                    memory.add_reminder(original, remind_time)
                    return f"Reminder set: {original} at {remind_time.strftime('%Y-%m-%d %H:%M')}, sir"
                else:
                    # Default 10 minutes from now
                    original = self._extract_original(text, raw)
                    rt = datetime.datetime.now() + datetime.timedelta(minutes=10)
                    memory.add_reminder(original, rt)
                    return f"I'll remind you to {original} in 10 minutes. You can specify time like 'in 5 minutes' or 'at 3 pm' for better accuracy."

        # Notes / Remember
        if low.startswith("remember that") or low.startswith("note that") or "remember that" in low or "note that" in low:
            m = re.search(r"(?:remember|note)(?: that)? (.+)", low)
            if m:
                fact = m.group(1).strip()
                original_fact = self._extract_original(text, fact)
                # Try split key value?
                memory.learn_fact(f"note_{len(memory.data.get('learned_facts', {}))}", original_fact)
                return f"Noted: {original_fact}"

        # File creation
        if "create file" in low or "write file" in low or "new file" in low or "make a file" in low:
            # Extract filename and content?
            # Example: "create file test.txt with content hello world"
            m = re.search(r"(?:create|write|make|new) (?:a )?file (?:named )?(\S+)(?: with (?:content )?(.*))?", low)
            if m:
                fname = m.group(1).strip()
                content = m.group(2) if m.group(2) else ""
                # Remove quotes? Use original
                try:
                    path = Path.cwd() / fname
                    # Prevent writing outside? Allow but warn
                    path.write_text(content or f"# File created by JARVIS on {datetime.datetime.now()}\n")
                    return f"File {fname} created at {path}, sir"
                except Exception as e:
                    return f"Failed to create file: {e}"
            else:
                return "Please specify filename, e.g., 'create file notes.txt with content hello'"

        # Timer
        if "timer" in low or "alarm" in low:
            # Parse minutes
            m = re.search(r"(\d+)\s*(second|minute|hour)s?", low)
            if m:
                num = int(m.group(1))
                unit = m.group(2)
                delta = datetime.timedelta()
                if "second" in unit:
                    delta = datetime.timedelta(seconds=num)
                elif "minute" in unit:
                    delta = datetime.timedelta(minutes=num)
                elif "hour" in unit:
                    delta = datetime.timedelta(hours=num)
                remind_time = datetime.datetime.now() + delta
                memory.add_reminder(f"Timer for {num} {unit}", remind_time)
                return f"Timer set for {num} {unit}, sir"
            else:
                return "For how long? Say like 'set timer for 5 minutes'"

        return None

    def _try_calculate(self, text: str):
        low = text.lower()
        # Only if math keywords
        if not any(x in low for x in ["calculate", "what is", "plus", "minus", "multiply", "divide", "times", "+", "-", "*", "/", "math", "solve"]):
            return None
        
        # Extract math expression
        # Clean text -> keep numbers and operators
        # Support "what is 5 plus 3"
        expr = low
        expr = expr.replace("what is", "").replace("calculate", "").replace("math", "").replace("solve", "").strip()
        # Word to symbol
        replacements = {
            "plus": "+",
            "minus": "-",
            "times": "*",
            "multiply": "*",
            "multiplied by": "*",
            "x": "*",
            "divide": "/",
            "divided by": "/",
            "power": "**",
            "to the power": "**",
        }
        for word, sym in replacements.items():
            expr = expr.replace(word, sym)
        
        # Keep only math chars
        # Allow digits, operators, parentheses, dot, spaces
        cleaned = re.sub(r"[^0-9\+\-\*\/\(\)\.\s]", "", expr).strip()
        if not cleaned:
            return None
        # Avoid empty or just number
        if cleaned.isdigit():
            return None
        # Must have operator
        if not any(op in cleaned for op in ["+", "-", "*", "/"]):
            return None
        # Prevent too long
        if len(cleaned) > 100:
            return None
        
        try:
            # Safe eval using ast
            import ast
            # Check allowed nodes
            tree = ast.parse(cleaned, mode='eval')
            allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Mod, ast.FloorDiv)
            for node in ast.walk(tree):
                if not isinstance(node, allowed):
                    return None
            result = eval(cleaned, {"__builtins__": {}}, {})
            return f"The answer is {result}, sir"
        except Exception:
            return None

    def _parse_reminder(self, raw: str):
        """Parse reminder text and time. Returns (text, datetime)"""
        raw = raw.strip()
        now = datetime.datetime.now()
        
        # Pattern "X in Y minutes"
        m = re.search(r"(.+) in (\d+)\s*(minute|second|hour)s?", raw)
        if m:
            task = m.group(1).strip()
            num = int(m.group(2))
            unit = m.group(3)
            delta = datetime.timedelta(minutes=num) if "minute" in unit else datetime.timedelta(seconds=num) if "second" in unit else datetime.timedelta(hours=num)
            return task, now + delta
        
        # Pattern "X at 5 pm" or "X at 15:30"
        m = re.search(r"(.+) at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?", raw)
        if m:
            task = m.group(1).strip()
            hour = int(m.group(2))
            minute = int(m.group(3)) if m.group(3) else 0
            ampm = m.group(4)
            if ampm:
                if ampm == "pm" and hour < 12:
                    hour += 12
                if ampm == "am" and hour == 12:
                    hour = 0
            # Set time today, or tomorrow if past
            rt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if rt < now:
                rt += datetime.timedelta(days=1)
            return task, rt
        
        # No time found
        return raw, None

    def _extract_original(self, original_text: str, lowered_extract: str) -> str:
        """Try to get original casing from original_text based on lowered extract"""
        low_original = original_text.lower()
        idx = low_original.find(lowered_extract.lower())
        if idx != -1:
            return original_text[idx:idx+len(lowered_extract)].strip()
        return lowered_extract
