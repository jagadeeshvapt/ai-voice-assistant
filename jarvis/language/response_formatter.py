"""
JARVIS Language - Response Formatter
Formats tool results into spoken responses in English/Tanglish/Tamil
"""
import datetime
from typing import Dict, Any

class ResponseFormatter:
    def __init__(self):
        self.templates = {
            "open_application": {
                "en": "Opened {application}.",
                "ta-en": "{application} open panniten."
            },
            "close_application": {
                "en": "Closed {application}.",
                "ta-en": "{application} close panniten."
            },
            "control_volume": {
                "en": "Volume {action}.",
                "ta-en": "Volume {action} panniten."
            },
            "take_screenshot": {
                "en": "Screenshot taken and saved.",
                "ta-en": "Screenshot eduthuten, save panniten."
            },
            "lock_screen": {
                "en": "Screen locked.",
                "ta-en": "Screen lock panniten."
            },
            "shutdown_system": {
                "en": "Shutdown initiated, Sir. 10 seconds.",
                "ta-en": "Shutdown start panniten Sir, 10 seconds la."
            },
            "system_status": {
                "en": "System status: {result}",
                "ta-en": "System status: {result}"
            },
            "get_time": {
                "en": "It's {time}, Sir.",
                "ta-en": "Ippo time {time} Sir."
            },
        }

    def format_tool_result(self, intent_data: Dict, tool_result: Any, language: str = "en") -> str:
        intent = intent_data.get("intent", "")
        args = intent_data.get("arguments", {})
        
        # If tool already returned a spoken string, use it
        if isinstance(tool_result, str) and len(tool_result) < 300:
            return tool_result
        
        # If intent has pre-defined reply from LLM planner, use it if not empty
        pre_reply = intent_data.get("reply", "")
        if pre_reply:
            return pre_reply
        
        # Format based on intent
        lang = language if language in ("en", "ta-en", "ta") else "en"
        if lang == "ta":
            lang = "ta-en"  # Use tanglish for Tamil for now
        
        # Time intent special
        if intent == "get_time":
            now = datetime.datetime.now().strftime("%I:%M %p, %A")
            if lang == "ta-en":
                return f"Ippo time {now} Sir."
            return f"It's {now}, Sir."
        
        if intent == "get_date":
            now = datetime.datetime.now().strftime("%A, %B %d, %Y")
            if lang == "ta-en":
                return f"Innaiku date {now}."
            return f"Today is {now}."
        
        # System status
        if intent == "system_status":
            result_str = str(tool_result) if tool_result else "All systems nominal"
            if lang == "ta-en":
                return f"System status: {result_str}"
            return f"System status: {result_str}"
        
        # Try template
        if intent in self.templates:
            tmpl_dict = self.templates[intent]
            tmpl = tmpl_dict.get(lang, tmpl_dict.get("en", "{result}"))
            try:
                return tmpl.format(**args, result=str(tool_result)[:200])
            except:
                # Fallback
                return tmpl.format(result=str(tool_result)[:200]) if "{result}" in tmpl else tmpl
        
        # Generic fallback
        if tool_result:
            return str(tool_result)[:400]
        
        # Last resort
        if lang == "ta-en":
            return "Mudichiten Sir."
        return "Done, Sir."

    def format_confirmation_request(self, intent_data: Dict, language: str = "en") -> str:
        intent = intent_data.get("intent", "")
        lang = language
        
        dangerous_msgs = {
            "shutdown_system": {
                "en": "Shutdown will close all apps. Are you sure? Say yes to confirm.",
                "ta-en": "Shutdown panna ellam close aagum. Confirm pannalama? Yes sollunga."
            },
            "restart_system": {
                "en": "Restart will close all apps. Confirm?",
                "ta-en": "Restart panna ellam close aagum. Confirm pannalama?"
            },
            "file_operation": {
                "en": f"File operation {intent_data.get('arguments')} - This may delete or move files. Confirm?",
                "ta-en": "File delete/move panna poren. Confirm pannalama?"
            }
        }
        
        if intent in dangerous_msgs:
            return dangerous_msgs[intent].get(lang, dangerous_msgs[intent]["en"])
        
        if lang == "ta-en":
            return f"{intent} panna confirmation venum. Yes-nu sollunga Sir."
        return f"{intent} requires confirmation. Please say yes to proceed."

    def format_denial(self, language: str = "en") -> str:
        if language == "ta-en":
            return "Sari Sir, cancel panniten."
        return "Okay Sir, cancelled."

    def format_error(self, error_msg: str, language: str = "en") -> str:
        if "not found" in error_msg.lower():
            if language == "ta-en":
                return "Adhu kedaikala Sir. Vera yaedhavathu try pannalama?"
            return "Not found, Sir. Try something else?"
        
        if language == "ta-en":
            return f"Error vandhuchu Sir: {error_msg[:100]}. Vera command try pannunga."
        return f"Error, Sir: {error_msg[:100]}"

    def format_greeting(self, user_name: str = "Sir", language: str = "en") -> str:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            greet = "Good morning"
            ta_greet = "Kaalai vanakkam"
        elif 12 <= hour < 17:
            greet = "Good afternoon"
            ta_greet = "Madhiyam vanakkam"
        else:
            greet = "Good evening"
            ta_greet = "Maalai vanakkam"
        
        if language == "ta-en":
            return f"{ta_greet} {user_name}. Offline ready. Enna help venum?"
        return f"{greet} {user_name}. All systems offline ready. How can I help?"

# Singleton
_formatter = None

def get_response_formatter() -> ResponseFormatter:
    global _formatter
    if _formatter is None:
        _formatter = ResponseFormatter()
    return _formatter
