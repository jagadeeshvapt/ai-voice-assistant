"""
JARVIS Brain - LLM + Intent routing + Skill execution
"""
import re
import datetime
import random
from typing import Optional, Dict

from .config import config
from .utils import logger
from .memory import get_memory
from .skills.base import get_best_skill

# Try OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

class Brain:
    def __init__(self):
        self.memory = get_memory()
        self.openai_client = None
        
        if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                logger.info(f"OpenAI client initialized with model {config.OPENAI_MODEL}")
            except Exception as e:
                logger.error(f"OpenAI init failed: {e}")
                self.openai_client = None
        else:
            if not config.OPENAI_API_KEY:
                logger.info("OPENAI_API_KEY not set, using local intelligent brain")
            if not OPENAI_AVAILABLE:
                logger.info("openai package not installed, using local brain")

        # Personality prompt for LLM
        self.system_prompt = f"""
You are JARVIS - Just A Rather Very Intelligent System, personal AI assistant like in Iron Man movies.
Your user is {self.memory.data.get('user_name', 'Sir')}.
Your personality:
- Highly intelligent, witty, British butler style like Paul Bettany's JARVIS
- Concise, technical when needed, but friendly
- You refer to user as Sir (or their name if known)
- You are helpful, proactive, and have access to system controls, web, memory
- Never say you are Meta AI or ChatGPT, you are JARVIS
- If you don't know something, admit but offer to search
- Keep responses under 3 sentences unless explaining something complex
- You remember past conversations
- Current time: {datetime.datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}
- System: {config.JARVIS_NAME} v2.0 running
- For actions like opening apps, say you are doing it but underlying system skill will handle actual opening
- You can control computer, search web, tell weather, jokes, todo, reminders, emails, etc.

Context from recent conversations:
{{context}}

Additional facts learned about user:
{{facts}}
"""

    def _get_llm_context(self):
        context = self.memory.get_context_for_llm(6)
        facts = ""
        learned = self.memory.data.get("learned_facts", {})
        if learned:
            facts = "\n".join([f"{k}: {v}" for k, v in learned.items()][:10])
        prompt = self.system_prompt.replace("{context}", context).replace("{facts}", facts)
        return prompt

    def think_with_llm(self, user_input: str) -> Optional[str]:
        """If OpenAI available, use LLM brain"""
        if not self.openai_client:
            return None
        
        try:
            system_prompt = self._get_llm_context()
            
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=300,
                timeout=15
            )
            reply = response.choices[0].message.content.strip()
            logger.info(f"LLM response: {reply}")
            return reply
        except Exception as e:
            logger.error(f"LLM thinking failed: {e}")
            return None

    def think_local(self, user_input: str) -> str:
        """Local rule-based intelligent fallback - no API needed"""
        low = user_input.lower()

        # Greetings
        if any(w in low for w in ["hello", "hi jarvis", "hey jarvis", "hey", "hi there"]):
            greetings = [
                f"Hello {self.memory.data.get('user_name', 'Sir')}, how can I assist you today?",
                f"At your service, {self.memory.data.get('user_name', 'Sir')}. What do you need?",
                f"Good to hear from you, sir. All systems ready. How can I help?",
                f"{self.memory.data.get('user_name', 'Sir')}, I'm listening. What shall we do?"
            ]
            return random.choice(greetings)

        # Exit
        if any(w in low for w in ["exit", "quit", "goodbye", "bye jarvis", "sleep jarvis", "go to sleep"]):
            farewells = [
                "Going offline, sir. Call me if you need anything.",
                "Powering down to standby mode. Goodbye, sir.",
                "As you wish, sir. I'll be here if you need me.",
                "Shutting down voice interface. Have a great day, sir."
            ]
            return random.choice(farewells) + " __EXIT__"

        # Thanks
        if any(w in low for w in ["thank you", "thanks jarvis", "thanks"]):
            return random.choice([
                "You're welcome, sir. Happy to help.",
                "My pleasure, sir.",
                "Anytime, sir. That's what I'm here for."
            ])

        # Name handling
        if "my name is" in low or "i am" in low and len(low.split()) <= 5:
            m = re.search(r"(?:my name is|i am) (\w+)", low)
            if m:
                name = m.group(1).title()
                self.memory.set_user_name(name)
                return f"Nice to meet you, {name}. I'll remember that, sir."

        if "what is my name" in low or "who am i" in low:
            return f"Your name is {self.memory.data.get('user_name', 'Sir')}, sir. Unless you'd like me to call you something else?"

        # How are you handling time_date skill? But local override for generic questions
        # For other things, try skills - lower threshold for better UX
        skill, score = get_best_skill(user_input)
        if skill and score >= 1:
            try:
                result = skill.handle(user_input, {"memory": self.memory})
                if result:
                    return result
            except Exception as e:
                logger.error(f"Skill {skill.name} error: {e}")

        # No skill matched strongly, provide intelligent fallback
        # Try knowledge queries via web_search skill? Already attempted via skill matching but may be low score
        # Do generic responses
        fallbacks = [
            f"I'm not sure about '{user_input}' yet, sir. Could you rephrase or should I search the web for you?",
            f"Interesting query, sir. I don't have that information offline. Try saying 'search for {user_input}' and I'll look it up.",
            f"Hmm, I need more context for that, sir. Are you asking me to search, open something, or calculate?",
        ]
        
        # If question-like, suggest searching
        if "?" in user_input or low.startswith(("who", "what", "where", "when", "why", "how", "can you", "could you")):
            return f"Let me look that up for you, sir. Say 'search for {user_input}' or I can open browser and search."
        
        return random.choice(fallbacks)

    def process(self, user_input: str) -> str:
        """Main entry - process user input and return response"""
        if not user_input or not user_input.strip():
            return "Sorry sir, I didn't catch that"
        
        user_input = user_input.strip()
        
        # First try local intent for critical system actions (fast response)
        # We want skills to take priority for system control
        skill, score = get_best_skill(user_input)
        if skill and score >= 1 and skill.name in ("system_control", "time_date", "automation", "media", "weather", "knowledge", "web_search", "communication"):
            try:
                result = skill.handle(user_input, {"memory": self.memory})
                if result:
                    # Check for exit marker
                    if "__EXIT__" in result:
                        return result
                    self.memory.add_conversation(user_input, result)
                    return result
            except Exception as e:
                logger.error(f"Critical skill error {skill.name}: {e}")

        # Then try LLM if available for intelligent understanding
        llm_response = self.think_with_llm(user_input)
        if llm_response:
            # But also check if LLM response requires action? Let LLM decide but also parse intent
            # If LLM says it will open something, also execute skill behind scenes
            if skill and score >= 3:
                # Execute skill action but return LLM response + action result?
                try:
                    action_result = skill.handle(user_input, {"memory": self.memory})
                    if action_result and skill.name == "system_control":
                        # Task executed, but we return LLM response (LLM said it would do)
                        # Actually for system control, prefer action result if LLM didn't do action
                        pass
                except:
                    pass
            
            self.memory.add_conversation(user_input, llm_response)
            
            # Check for exit marker in LLM too
            if any(w in user_input.lower() for w in ["exit", "quit", "goodbye", "bye"]):
                if "goodbye" in llm_response.lower() or "offline" in llm_response.lower():
                    return llm_response + " __EXIT__"
            
            return llm_response

        # Fallback to local brain (skills + rule-based)
        local_response = self.think_local(user_input)
        
        # Store in memory unless it's error
        if local_response and "didn't catch" not in local_response:
            self.memory.add_conversation(user_input, local_response.replace(" __EXIT__", ""))
        
        return local_response


# Singleton
brain_instance = None

def get_brain() -> Brain:
    global brain_instance
    if brain_instance is None:
        brain_instance = Brain()
    return brain_instance
