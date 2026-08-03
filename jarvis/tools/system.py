"""
JARVIS Tools - System monitoring, info, local only
"""
import platform
import datetime
from typing import Dict
from .registry import Tool
from ..utils import logger

class SystemTool(Tool):
    name = "system_status"
    description = "Shows system status: CPU, RAM, disk, battery"
    dangerous = False
    required_permission = 0

    def validate(self, args):
        pass

    def execute(self, args):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            battery = None
            try:
                battery = psutil.sensors_battery()
            except:
                pass
            
            status = f"CPU {cpu}%, RAM {ram.percent}% used ({ram.available//1024//1024}MB free), Disk {disk.percent}% used"
            if battery:
                status += f", Battery {battery.percent}% {'charging' if battery.power_plugged else ''}"
            status += f", System {platform.system()} {platform.release()}"
            return status
        except Exception as e:
            return f"System: {platform.system()} {platform.release()}, Time {datetime.datetime.now().strftime('%I:%M %p')}, Error getting detailed stats: {e}"

class GetTimeTool(Tool):
    name = "get_time"
    required_permission = 0
    def validate(self, args): pass
    def execute(self, args):
        now = datetime.datetime.now()
        return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d')}"

class GetDateTool(Tool):
    name = "get_date"
    required_permission = 0
    def validate(self, args): pass
    def execute(self, args):
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}"

# Reminder / Timer tools (wrap memory reminders)

class SetReminderTool(Tool):
    name = "set_reminder"
    description = "Sets a reminder"
    required_permission = 1
    def validate(self, args): pass
    def execute(self, args):
        from ..memory.reminders import get_reminder_manager
        import re
        from datetime import datetime, timedelta
        
        text = args.get("text") or args.get("raw") or "Reminder"
        time_str = args.get("time") or args.get("relative") or ""
        
        # Parse time like "in 5 minutes", "at 3pm", "6 manikku"
        now = datetime.now()
        remind_time = now + timedelta(minutes=10)  # default 10 min
        
        # Try parse
        if time_str:
            m = re.search(r"(\d+)\s*(minute|hour|second)", str(time_str), re.IGNORECASE)
            if m:
                num = int(m.group(1))
                unit = m.group(2).lower()
                if "minute" in unit:
                    remind_time = now + timedelta(minutes=num)
                elif "hour" in unit:
                    remind_time = now + timedelta(hours=num)
                elif "second" in unit:
                    remind_time = now + timedelta(seconds=num)
            else:
                # Try "at HH"
                m = re.search(r"(\d{1,2})(?:\s*:\s*(\d{2}))?\s*(am|pm)?", str(time_str), re.IGNORECASE)
                if m:
                    h = int(m.group(1))
                    mm = int(m.group(2)) if m.group(2) else 0
                    ampm = m.group(3)
                    if ampm:
                        if ampm.lower() == "pm" and h < 12:
                            h += 12
                        if ampm.lower() == "am" and h == 12:
                            h = 0
                    try:
                        rt = now.replace(hour=h, minute=mm, second=0, microsecond=0)
                        if rt < now:
                            rt += timedelta(days=1)
                        remind_time = rt
                    except:
                        pass
        
        manager = get_reminder_manager()
        manager.add_reminder(text, remind_time)
        return f"Reminder set panniten: {text} at {remind_time.strftime('%I:%M %p')}"

class SetTimerTool(Tool):
    name = "set_timer"
    required_permission = 1
    def validate(self, args): pass
    def execute(self, args):
        from ..memory.reminders import get_reminder_manager
        import re
        
        duration = args.get("duration") or "5"
        unit = args.get("unit") or "minutes"
        raw = args.get("raw") or ""
        
        # Extract number
        m = re.search(r"(\d+)", str(duration))
        if not m:
            m = re.search(r"(\d+)", raw)
        num = int(m.group(1)) if m else 5
        
        # Determine seconds
        if "second" in str(unit).lower() or "second" in raw.lower():
            secs = num
        elif "hour" in str(unit).lower() or "hour" in raw.lower():
            secs = num * 3600
        else:
            secs = num * 60
        
        manager = get_reminder_manager()
        manager.add_timer(secs, f"Timer {num} {unit}")
        return f"{num} {unit} timer set panniten Sir."

class KnowledgeQueryTool(Tool):
    name = "knowledge_query"
    required_permission = 0
    def validate(self, args): pass
    def execute(self, args):
        query = args.get("query") or args.get("raw") or ""
        # Try local knowledge base first
        try:
            from ..memory.knowledge_base import get_knowledge_base
            kb = get_knowledge_base()
            results = kb.search(query)
            if results:
                return f"Local knowledge base la irundhu: {results[0]['title']} - {results[0]['content'][:300]}"
        except:
            pass
        
        # Fallback to offline answer
        return f"'{query}' pathi offline la detailed answer illa Sir. Local notes index pannunga or internet search use pannalam, but offline mode la off panniten."
