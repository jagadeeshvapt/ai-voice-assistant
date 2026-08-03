"""
JARVIS Language - Intent Parser - Human Brain with Full Knowledge Domains
- Quick commands (no LLM) for low latency
- Regex intent extraction for all domains: laptop + investment + business + medical + legal + AI
- Returns structured JSON per spec
"""
import re
from typing import Dict, Optional
from ..utils import logger

class IntentParser:
    def __init__(self):
        self.quick_commands = {
            # Time - improved for natural speech like "what is the time right now", "time and what is the time"
            r"what.*time|time.*what|current time|time right now|enna time|time enna|time sollu": {"intent": "get_time", "permission_level": 0},
            r"^(date|innaiku enna date|today date)": {"intent": "get_date", "permission_level": 0},
            r"^(system status|status sollu|system info)": {"intent": "system_status", "permission_level": 0},
            r"volume up|sound kuda|satham kuda": {"intent": "control_volume", "args": {"action": "up"}, "permission_level": 1},
            r"volume down|sound kammi|satham kammi|volume kammi": {"intent": "control_volume", "args": {"action": "down"}, "permission_level": 1},
            r"mute|sound off|satham off": {"intent": "control_volume", "args": {"action": "mute"}, "permission_level": 1},
            r"unmute|sound on|satham on": {"intent": "control_volume", "args": {"action": "unmute"}, "permission_level": 1},
            r"set volume (\d+)": {"intent": "control_volume", "args": {"action": "set", "level": "{group1}"}, "permission_level": 1, "regex": True},
            r"volume (\d+)(?: percent)?": {"intent": "control_volume", "args": {"action": "set", "level": "{group1}"}, "permission_level": 1, "regex": True},
            r"lock screen|screen lock|lock pannu": {"intent": "lock_screen", "permission_level": 1},
            r"take screenshot|screenshot edu": {"intent": "take_screenshot", "permission_level": 1},
            r"open browser|browser open": {"intent": "open_application", "args": {"application": "chrome"}, "permission_level": 1},
            r"pause music|music pause|pause pannu": {"intent": "control_media", "args": {"action": "pause"}, "permission_level": 1},
            r"play music|music play|play pannu": {"intent": "control_media", "args": {"action": "play"}, "permission_level": 1},
            r"next song|next track|adutha song": {"intent": "control_media", "args": {"action": "next"}, "permission_level": 1},
            # Single word apps - real JARVIS should open if just app name said
            r"^chrome$|^google chrome$": {"intent": "open_application", "args": {"application": "chrome"}, "permission_level": 1},
            r"^notepad$": {"intent": "open_application", "args": {"application": "notepad"}, "permission_level": 1},
            r"^youtube$": {"intent": "open_application", "args": {"application": "youtube"}, "permission_level": 1},
            r"^calculator$": {"intent": "open_application", "args": {"application": "calculator"}, "permission_level": 1},
        }
        
        self.intent_patterns = [
            # Self-learning - highest priority
            {"pattern": r"show\s+mistakes|list\s+mistakes|view\s+mistakes", "intent": "show_mistakes", "args_map": {}, "permission": 0, "confidence": 0.99},
            {"pattern": r"show\s+lessons|list\s+lessons|view\s+lessons", "intent": "show_lessons", "args_map": {}, "permission": 0, "confidence": 0.99},
            {"pattern": r"self\s*learning|learning\s*stats", "intent": "self_learning", "args_map": {}, "permission": 0, "confidence": 0.99},
            # Knowledge domains - high priority for human-like full AI
            {"pattern": r"(?:investment|stock|mutual fund|crypto|trading|share market|sip|gold|real estate|portfolio).*", "intent": "investment_advice", "args_map": {"query": 0}, "permission": 0, "confidence": 0.9},
            {"pattern": r"(?:business|startup|entrepreneur|marketing|business plan|funding).*", "intent": "business_advice", "args_map": {"query": 0}, "permission": 0, "confidence": 0.9},
            {"pattern": r"(?:doctor|health|medical|symptom|fever|pain|first aid|mental health).*", "intent": "medical_info", "args_map": {"query": 0}, "permission": 0, "confidence": 0.85},
            {"pattern": r"(?:lawyer|legal|law|ipc|rights|contract|cyber law|property|consumer).*", "intent": "legal_info", "args_map": {"query": 0}, "permission": 0, "confidence": 0.85},
            {"pattern": r"(?:police|fir|complaint|arrest).*", "intent": "police_info", "args_map": {"query": 0}, "permission": 0, "confidence": 0.85},
            {"pattern": r"(?:court|bail|judge|case|trial).*", "intent": "court_info", "args_map": {"query": 0}, "permission": 0, "confidence": 0.85},
            {"pattern": r"(?:ai|artificial intelligence|machine learning|how to build jarvis|autonomous agent|voice ai|llm).*", "intent": "ai_technology", "args_map": {"query": 0}, "permission": 0, "confidence": 0.9},
            {"pattern": r"(?:stress|sad|happy|angry|anxious|depressed|motivation|lonely|emotion|feel|depression).*", "intent": "psychology_advice", "args_map": {"query": 0}, "permission": 0, "confidence": 0.8},
            {"pattern": r"(?:software|programming|coding|python|system design|security|windows control).*", "intent": "software_knowledge", "args_map": {"query": 0}, "permission": 0, "confidence": 0.85},
            {"pattern": r"(?:technology|tech|cloud|networking|latest tech).*", "intent": "technology_knowledge", "args_map": {"query": 0}, "permission": 0, "confidence": 0.85},
            # Applications
            {"pattern": r"(?:open|launch|start)\s+(?:the\s+)?(.+?)(?:\s+application|\s+app)?$", "intent": "open_application", "args_map": {"application": 1}, "permission": 1, "confidence": 0.95},
            {"pattern": r"(.+?)\s+open(?:\s+pannu|\s+panni|\s+pannidu)?$", "intent": "open_application", "args_map": {"application": 1}, "permission": 1, "confidence": 0.92},
            {"pattern": r"(.+?)\s+open pannu", "intent": "open_application", "args_map": {"application": 1}, "permission": 1, "confidence": 0.9},
            {"pattern": r"close\s+(?:the\s+)?(.+)", "intent": "close_application", "args_map": {"application": 1}, "permission": 1, "confidence": 0.85},
            {"pattern": r"(.+?)\s+close pannu", "intent": "close_application", "args_map": {"application": 1}, "permission": 1, "confidence": 0.9},
            # Browser
            {"pattern": r"(?:search|google|youtube).*?(?:for)?\s+(.+?)\s+on\s+(youtube|google)", "intent": "browser_search", "args_map": {"query": 1, "engine": 2}, "permission": 1, "confidence": 0.9},
            {"pattern": r"open website\s+(.+)", "intent": "open_website", "args_map": {"url": 1}, "permission": 1, "confidence": 0.9},
            # Files - FULL ACCESS
            {"pattern": r"list folders?\s*(.+)?", "intent": "list_folders", "args_map": {"path": 1}, "permission": 0, "confidence": 0.9},
            {"pattern": r"(?:create|make).*?folder\s+(?:named\s+)?(.+)", "intent": "create_folder", "args_map": {"name": 1}, "permission": 1, "confidence": 0.85},
            {"pattern": r"search files?\s*(?:for)?\s*(.+)", "intent": "search_files", "args_map": {"query": 1}, "permission": 0, "confidence": 0.9},
            {"pattern": r"(?:rename|move|delete)\s+file\s+(.+)", "intent": "file_operation", "args_map": {"target": 1}, "permission": 2, "confidence": 0.8},
            {"pattern": r"read file\s+(.+)", "intent": "read_file", "args_map": {"name": 1}, "permission": 0, "confidence": 0.9},
            # Reminders
            {"pattern": r"remind me to (.+?)(?: at (\d+.*)| in (\d+.*))?$", "intent": "set_reminder", "args_map": {"text": 1, "time": 2}, "permission": 1, "confidence": 0.9},
            {"pattern": r"(\d+)\s*(?:minutes?|hours?|seconds?)\s*timer", "intent": "set_timer", "args_map": {"duration": 1}, "permission": 1, "confidence": 0.9},
            # Media
            {"pattern": r"play\s+(?:song\s+)?(.+?)\s+on\s+youtube", "intent": "play_youtube", "args_map": {"query": 1}, "permission": 1, "confidence": 0.9},
            {"pattern": r"play\s+(.+)", "intent": "play_media", "args_map": {"query": 1}, "permission": 1, "confidence": 0.7},
            # System - FULL ACCESS
            {"pattern": r"shutdown|power off", "intent": "shutdown_system", "args_map": {}, "permission": 3, "confidence": 0.95},
            {"pattern": r"restart|reboot", "intent": "restart_system", "args_map": {}, "permission": 3, "confidence": 0.9},
            {"pattern": r"sleep|hibernate", "intent": "sleep_system", "args_map": {}, "permission": 2, "confidence": 0.85},
            # Autonomous
            {"pattern": r"(?:build|create).*(?:project|portfolio|website|app).*", "intent": "autonomous_agent", "args_map": {"goal": 0}, "permission": 1, "confidence": 0.85},
            {"pattern": r"what is (.+)", "intent": "knowledge_query", "args_map": {"query": 1}, "permission": 0, "confidence": 0.6},
        ]

    def _extract_args(self, match, args_map):
        args = {}
        for key, idx in args_map.items():
            if isinstance(idx, int):
                try:
                    args[key] = match.group(idx).strip() if match.group(idx) else None
                    if key == "query" and args[key] == match.group(0):
                        args[key] = match.group(0)
                except:
                    args[key] = None
            else:
                args[key] = idx
        for k, v in list(args.items()):
            if isinstance(v, str) and "{group" in v:
                for i in range(1,5):
                    ph = f"{{group{i}}}"
                    if ph in v:
                        try:
                            args[k] = match.group(i)
                        except:
                            pass
        return args

    def parse(self, normalized_text, raw_text=None):
        text = normalized_text.lower().strip()
        if not text:
            return None
        # Quick commands
        for pattern, data in self.quick_commands.items():
            try:
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    args = data.get("args", {}).copy()
                    if data.get("regex"):
                        for k,v in args.items():
                            if "{group" in str(v):
                                try:
                                    args[k] = m.group(1)
                                except:
                                    pass
                    args["raw"] = raw_text or normalized_text
                    return {"intent": data["intent"], "arguments": args, "language": "ta-en" if "pannu" in (raw_text or "") else "en", "confidence": 0.98, "requires_confirmation": False, "permission_level": data.get("permission_level",1), "reply":"", "is_quick": True}
            except:
                pass
        # Full patterns best match
        best = None
        best_score = 0
        for entry in self.intent_patterns:
            try:
                m = re.search(entry["pattern"], text, re.IGNORECASE)
                if m:
                    conf = entry.get("confidence",0.8)
                    if conf > best_score:
                        best_score = conf
                        args = self._extract_args(m, entry.get("args_map",{}))
                        args["raw"] = raw_text or normalized_text
                        if "query" not in args or not args["query"]:
                            args["query"] = raw_text or normalized_text
                        best = {"intent": entry["intent"], "arguments": args, "language": "ta-en", "confidence": conf, "requires_confirmation": entry.get("permission",1)>=2, "permission_level": entry.get("permission",1), "reply":"", "pattern_matched": entry["pattern"]}
            except Exception as e:
                continue
        if best:
            if best["intent"] in ["shutdown_system","restart_system"]:
                best["permission_level"]=3
                best["requires_confirmation"]=True
            return best
        if "open" in text:
            m = re.search(r"open (.+)", text)
            if m:
                return {"intent": "open_application", "arguments": {"application": m.group(1).strip(), "raw": raw_text or text}, "language":"en","confidence":0.6,"requires_confirmation":False,"permission_level":1,"reply":""}
        return None

_intent_parser = None
def get_intent_parser():
    global _intent_parser
    if _intent_parser is None:
        _intent_parser = IntentParser()
    return _intent_parser
