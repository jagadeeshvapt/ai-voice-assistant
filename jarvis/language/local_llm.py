"""
JARVIS Language - Local LLM Planner - Human-like AGI Brain
Uses llama.cpp if available, otherwise rule-based planner with full domain knowledge
Returns structured JSON intent, never executes directly
"""

import os
import json
import re
from typing import Dict, Optional
from ..config import config
from ..utils import logger

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None

class LocalLLM:
    def __init__(self):
        self.model_path = config.LLM_MODEL_PATH
        self.engine = config.LLM_ENGINE
        self._llama = None
        self._fallback_active = True
        
        if self.engine == "llama.cpp" and LLAMA_CPP_AVAILABLE:
            if self.model_path.exists():
                try:
                    self._llama = Llama(
                        model_path=str(self.model_path),
                        n_ctx=2048,
                        n_threads=os.cpu_count() or 4,
                        verbose=False,
                        n_gpu_layers=0
                    )
                    self._fallback_active = False
                    logger.info(f"Local LLM loaded: {self.model_path}")
                except Exception as e:
                    logger.error(f"Llama load failed: {e}, using rule-based fallback")
            else:
                logger.warning(f"LLM model not found at {self.model_path}, using rule-based fallback")
        else:
            logger.info(f"LLM fallback mode: engine={self.engine}, llama_available={LLAMA_CPP_AVAILABLE}")

    def _rule_based_planner(self, text: str, context: str = "") -> Dict:
        low = text.lower().strip()
        
        # REAL JARVIS FIX: Handle time queries very early - highest priority
        # User says: "what time is it", "time and what is the time right now", "enna time", "time right now"
        if any(phrase in low for phrase in ["what time", "enna time", "time right now", "current time", "time now", "what's the time", "time sollu", "time enna"]):
            # Make sure it's not part of larger unrelated query
            if "time" in low and len(low.split()) <= 10:
                is_tanglish = any(w in low for w in ["pannu", "panni", "enna", "konjam", "romba", "da", "di", "manikku", "podu", "sollu"])
                lang = "ta-en" if is_tanglish else "en"
                return {"intent": "get_time", "arguments": {"raw": text}, "language": lang, "confidence": 0.99, "requires_confirmation": False, "permission_level": 0, "reply": ""}
        
        # Handle single app names like "chrome" alone - real JARVIS should open
        single_apps = ["chrome", "notepad", "youtube", "calculator", "firefox", "edge", "vscode", "spotify", "vlc"]
        if low.strip() in single_apps:
            is_tanglish = any(w in low for w in ["pannu", "panni", "enna"])
            lang = "ta-en" if is_tanglish else "en"
            return {"intent": "open_application", "arguments": {"application": low.strip(), "raw": text}, "language": lang, "confidence": 0.95, "requires_confirmation": False, "permission_level": 1, "reply": f"{low.strip().title()} open pannuren." if is_tanglish else f"Opening {low.strip()}."}
        
        # Human brain: detect emotion and domain first

        is_tanglish = any(w in low for w in ["pannu", "panni", "enna", "konjam", "romba", "da", "di", "manikku", "podu"])
        lang = "ta-en" if is_tanglish else "en"
        
        if any(w in low for w in ["shutdown", "power off", "switch off computer"]):
            return {"intent": "shutdown_system", "arguments": {"raw": text}, "language": lang, "confidence": 0.98, "requires_confirmation": True, "permission_level": 3, "reply": "Computer shutdown panna confirmation venum. Confirm pannunga." if is_tanglish else "Shutdown requires confirmation. Please confirm."}
        if "restart" in low or "reboot" in low:
            return {"intent": "restart_system", "arguments": {"raw": text}, "language": lang, "confidence": 0.95, "requires_confirmation": True, "permission_level": 3, "reply": "Restart confirmation venum." if is_tanglish else "Restart requires confirmation."}
        m = re.search(r"open (?:the )?(.+)", low)
        if m and len(low.split()) < 6:
            app_name = m.group(1).strip().replace("application","").replace("app","").strip()
            return {"intent": "open_application", "arguments": {"application": app_name, "raw": text}, "language": lang, "confidence": 0.9, "requires_confirmation": False, "permission_level": 1, "reply": f"{app_name.title()} open pannuren." if is_tanglish else f"Opening {app_name}."}
        m = re.search(r"close (?:the )?(.+)", low)
        if m:
            return {"intent": "close_application", "arguments": {"application": m.group(1).strip(), "raw": text}, "language": lang, "confidence": 0.85, "requires_confirmation": False, "permission_level": 1, "reply": f"{m.group(1)} close pannuren." if is_tanglish else f"Closing {m.group(1)}."}
        if "volume" in low or "sound" in low or "satham" in low:
            if "up" in low or "kuda" in low or "jaasti" in low or "increase" in low:
                return {"intent": "control_volume", "arguments": {"action": "up", "raw": text}, "language": lang, "confidence": 0.9, "requires_confirmation": False, "permission_level": 1, "reply": "Volume jaasthi panniten." if is_tanglish else "Volume increased."}
            if "down" in low or "kammi" in low or "kura" in low or "decrease" in low:
                return {"intent": "control_volume", "arguments": {"action": "down", "raw": text}, "language": lang, "confidence": 0.9, "requires_confirmation": False, "permission_level": 1, "reply": "Volume kammi panniten." if is_tanglish else "Volume decreased."}
            m = re.search(r"(\d+)", low)
            if m:
                return {"intent": "control_volume", "arguments": {"action": "set", "level": m.group(1), "raw": text}, "language": lang, "confidence": 0.9, "requires_confirmation": False, "permission_level": 1, "reply": f"Volume {m.group(1)} set panniten." if is_tanglish else f"Volume set to {m.group(1)}."}
        if "screenshot" in low:
            return {"intent": "take_screenshot", "arguments": {"raw": text}, "language": lang, "confidence": 0.95, "requires_confirmation": False, "permission_level": 1, "reply": "Screenshot eduthuten." if is_tanglish else "Screenshot taken."}
        if "lock" in low:
            return {"intent": "lock_screen", "arguments": {"raw": text}, "language": lang, "confidence": 0.9, "requires_confirmation": False, "permission_level": 1, "reply": "Screen lock panniten." if is_tanglish else "Screen locked."}
        if "reminder" in low or "alarm" in low:
            return {"intent": "set_reminder", "arguments": {"raw": text, "text": text}, "language": lang, "confidence": 0.8, "requires_confirmation": False, "permission_level": 1, "reply": "Reminder vechukiten." if is_tanglish else "Reminder set."}
        if "timer" in low:
            m = re.search(r"(\d+)", low)
            if m:
                return {"intent": "set_timer", "arguments": {"duration": m.group(1), "raw": text}, "language": lang, "confidence": 0.9, "requires_confirmation": False, "permission_level": 1, "reply": f"{m.group(1)} minutes timer set panniten." if is_tanglish else f"Timer set for {m.group(1)}."}
        if "search" in low or "youtube" in low or "google" in low:
            m = re.search(r"search (?:for)?(.*)", low)
            query = m.group(1).strip() if m else text
            engine = "youtube" if "youtube" in low else "google"
            return {"intent": "browser_search", "arguments": {"query": query, "engine": engine, "raw": text}, "language": lang, "confidence": 0.75, "requires_confirmation": False, "permission_level": 1, "reply": f"{query} search pannuren {engine} la." if is_tanglish else f"Searching {query} on {engine}."}
        if any(w in low for w in ["create file", "create folder", "make folder", "new file"]):
            return {"intent": "create_file" if "file" in low else "create_folder", "arguments": {"raw": text}, "language": lang, "confidence": 0.7, "requires_confirmation": False, "permission_level": 1, "reply": "File create pannuren." if is_tanglish else "Creating file."}
        if "system status" in low or "cpu" in low or "ram" in low:
            return {"intent": "system_status", "arguments": {"raw": text}, "language": lang, "confidence": 0.85, "requires_confirmation": False, "permission_level": 0, "reply": ""}
        if "time" in low:
            return {"intent": "get_time", "arguments": {"raw": text}, "language": lang, "confidence": 0.95, "requires_confirmation": False, "permission_level": 0, "reply": ""}
        return {"intent": "knowledge_query", "arguments": {"query": text, "raw": text}, "language": lang, "confidence": 0.4, "requires_confirmation": False, "permission_level": 0, "reply": "Ippo idhu offline mode la mudiyala, but try pannuren." if is_tanglish else "I'm offline but I'll try local knowledge."}

    def _llm_inference(self, text: str, context: str = ""):
        if not self._llama:
            return None
        try:
            from .human_personality import get_human_system_prompt, detect_emotion
            import datetime
            emotion = detect_emotion(text)
            user_name = "Sir"
            try:
                from ..memory.database import get_memory_db
                db = get_memory_db()
                user_name = db.get_user_name()
            except:
                pass
            human_prompt = get_human_system_prompt(user_name=user_name, current_time=datetime.datetime.now().strftime("%A %B %d %Y %I:%M %p"), language="ta-en" if any(w in text.lower() for w in ["pannu","enna"]) else "en", context=context, emotion=emotion)
            system_prompt = f"""{human_prompt}

You output ONLY JSON:
{{
  "intent": "open_application",
  "arguments": {{"application": "chrome"}},
  "language": "ta-en",
  "confidence": 0.96,
  "requires_confirmation": false,
  "permission_level": 1,
  "reply": "Chrome open pannuren.",
  "emotion": "neutral"
}}

Allowed intents: open_application, close_application, control_volume, take_screenshot, lock_screen, shutdown_system, restart_system, set_reminder, set_timer, browser_search, search_files, create_file, create_folder, system_status, get_time, play_youtube, play_media, knowledge_query, investment_advice, business_advice, software_knowledge, technology_knowledge, medical_info, legal_info, police_info, court_info, ai_technology, psychology_advice, autonomous_agent

Context: {context}
User: {text}
Emotion: {emotion}
JSON:"""
            output = self._llama(system_prompt, max_tokens=300, temperature=0.2, stop=["\n\n", "User:"])
            raw = output['choices'][0]['text'].strip()
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                j = json.loads(json_match.group())
                if "intent" in j and "arguments" in j:
                    return j
            return None
        except Exception as e:
            logger.error(f"LLM inference error: {e}")
            return None

    def plan(self, text: str, context: str = ""):
        if not self._fallback_active:
            result = self._llm_inference(text, context)
            if result:
                logger.info(f"LLM planned: {result}")
                return result
        result = self._rule_based_planner(text, context)
        logger.info(f"Rule-based planned: {result}")
        return result

_llm_instance = None
def get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LocalLLM()
    return _llm_instance
