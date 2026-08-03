import datetime
import random
from .base import Skill, register_skill

@register_skill
class TimeDateSkill(Skill):
    name = "time_date"
    description = "Tells time, date, day, greeting and small talk"
    keywords = ["time", "date", "day", "month", "year", "what time", "current time", "today", "clock", "greeting", "good morning", "good evening", "how are you", "who are you", "what are you"]
    patterns = [
        r"what('s| is) the time",
        r"what('s| is) today",
        r"what day is it",
        r"tell me (the )?time",
        r"current time",
    ]

    def handle(self, text, context=None):
        low = text.lower()
        
        now = datetime.datetime.now()
        
        if "time" in low:
            return f"It's {now.strftime('%I:%M %p')} {now.strftime('%A')}, sir"
        
        if "date" in low or "today" in low or "day" in low:
            return f"Today is {now.strftime('%A, %B %d, %Y')}"
        
        if any(x in low for x in ["who are you", "what are you"]):
            return "I am JARVIS, your personal AI assistant. Just A Rather Very Intelligent System. I'm here to help you with everything, sir."
        
        if "how are you" in low:
            responses = [
                "I'm running at optimal efficiency sir, ready to assist you.",
                "All systems nominal, sir. How can I help you today?",
                "I am functional and ready, sir. Thank you for asking.",
            ]
            return random.choice(responses)
        
        if "good morning" in low or "good afternoon" in low or "good evening" in low:
            hour = now.hour
            if 5 <= hour < 12:
                return "Good morning sir, hope your day is going great!"
            elif 12 <= hour < 17:
                return "Good afternoon sir!"
            else:
                return "Good evening sir!"
        
        return f"It's {now.strftime('%A, %B %d, %Y - %I:%M %p')}"
