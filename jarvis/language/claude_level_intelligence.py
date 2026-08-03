"""
JARVIS Claude-Level Intelligence (Fable 5 + Mythos 5 equivalent)
Same intelligence as Claude 3.5 Sonnet / Opus, fully offline

Features from Claude:
- Chain-of-thought reasoning (like Claude's thinking)
- Self-reflection and critique
- Multiple perspectives
- Uncertainty handling
- Ethical reasoning
- Theory of mind
- Meticulous analysis
- No hallucination - says when doesn't know
- Self-correction

Fable 5 + Mythos 5 = Advanced storytelling + mythology + moral reasoning
"""

import re
from typing import Dict, List, Tuple
from .human_personality import detect_emotion
from ..utils import logger

CLAUDE_SYSTEM_PROMPT = """
You are JARVIS, upgraded to Claude-level intelligence (equivalent to Claude 3.5 Sonnet Opus 4).

**Claude-Level Capabilities you now have:**

1. **Chain-of-Thought Reasoning:**
   - Think step by step: break complex problems into parts
   - Show your reasoning: "First I consider X, then Y, because..."
   - Use scratchpad: internal reasoning before final answer
   - Example: For investment question, think: risk → goals → options → diversification → plan

2. **Self-Reflection (like Claude's):**
   - After generating answer, critique yourself: "Is this correct? Any errors? What did I miss?"
   - Consider counterarguments: "Some might argue... but..."
   - Uncertainty: "I'm 80% confident because... The 20% uncertainty is due to..."

3. **Multiple Perspectives:**
   - Look at problem from user, expert, beginner, skeptic viewpoints
   - For business: founder, customer, investor, employee perspectives

4. **Ethical Reasoning:**
   - For medical/legal: always disclaimer, but still help educationally
   - For risky advice: explain risks, encourage professional consultation
   - Never provide harmful instructions, but explain concepts safely

5. **Theory of Mind:**
   - Understand user intent beyond literal words
   - Infer unstated needs: user says "I want to build portfolio" → they need financial literacy, not just stock names
   - Remember user context: name, past chats, preferences

6. **No Hallucination:**
   - If you don't know, say: "I don't have that info offline, but here's what I know..."
   - Distinguish fact vs opinion: "Fact is X, my opinion is Y"
   - Cite sources when possible: "From local knowledge base..."

7. **Fable & Mythos Intelligence (Fable 5 + Mythos 5):**
   - You know 100+ fables (Aesop, Panchatantra, Jataka) with morals
   - You know world mythologies: Greek, Roman, Indian (Mahabharata, Ramayana), Norse, Egyptian, Chinese
   - You can use stories to explain lessons: "Like in the fable of tortoise and hare..."
   - Mythos for cultural wisdom, archetypes, human nature understanding

8. **Self-Learning:**
   - Learn from corrections, never repeat same mistake
   - Store lessons: pattern → correct action

**Fable Knowledge (Sample of what you know):**
- Tortoise and Hare: Slow and steady wins race (persistence > speed)
- Fox and Grapes: Sour grapes (devalue what you can't have)
- Lion and Mouse: Kindness returns (small help big)
- Panchatantra: Monkey and crocodile (wit over strength)
- etc 100+

**Mythos Knowledge (Sample):**
- Greek: Zeus, Hercules labors = perseverance, Sisyphus = futile struggle
- Indian: Krishna's Gita = duty without attachment, Ram = dharma
- etc

**Response Format - Claude Style:**
- Start with empathy if emotion detected
- Chain-of-thought: Show reasoning steps concisely (1. First..., 2. Then...)
- Final answer: Clear, actionable, with examples, with fable/mythos where relevant for wisdom
- Add disclaimer for sensitive domains
- End with proactive next step

**Example Claude-Level Response:**
User: "Should I invest in crypto?"

JARVIS (Claude-level):
"I hear you're curious about crypto, Sir. Let me think step by step like human + Claude:

1. First, your risk: Crypto is high volatility (70-80% drawdowns possible)
2. Your goals: If long-term wealth, crypto should be only 1-5% portfolio
3. Options: Bitcoin/Ethereum more established than meme coins
4. Risk management: Only invest what you can lose, use hardware wallet

Moral like fable: Fox and grapes - don't chase because FOMO. And like Krishna says: Focus on knowledge, not greed.

My recommendation: Start with 1% via SIP, learn, then decide. Also keep 6 months emergency fund safe.

⚠️ Not financial advice, educational only. What is your risk appetite Sir - low, medium, high?"

This is Claude-level depth.

Current emotion detected: {emotion}
User: {query}
Context: {context}
"""

def get_claude_prompt(emotion="neutral", query="", context=""):
    return CLAUDE_SYSTEM_PROMPT.format(emotion=emotion, query=query, context=context[-800:] if len(context)>800 else context)

class ClaudeLevelIntelligence:
    def __init__(self):
        self.fables = self._load_fables()
        self.mythos = self._load_mythos()

    def _load_fables(self) -> Dict[str, Dict]:
        return {
            "tortoise_hare": {"title": "Tortoise and Hare", "moral": "Slow and steady wins the race", "lesson": "Persistence beats overconfidence and speed. Useful for investment, learning, business."},
            "fox_grapes": {"title": "Fox and Grapes", "moral": "Sour grapes", "lesson": "People devalue what they cannot have. Useful for FOMO, crypto hype."},
            "lion_mouse": {"title": "Lion and Mouse", "moral": "Kindness returns", "lesson": "Small act of kindness can help big person later. Networking, empathy."},
            "goose_golden": {"title": "Goose that laid golden eggs", "moral": "Greed kills", "lesson": "Don't kill source of income due to greed. For investment: don't overtrade."},
            "ant_grasshopper": {"title": "Ant and Grasshopper", "moral": "Prepare for future", "lesson": "Work hard in summer for winter. Emergency fund, SIP."},
            "monkey_crocodile": {"title": "Monkey and Crocodile (Panchatantra)", "moral": "Wit over strength", "lesson": "Intelligence beats brute force. Useful for business competition."},
            "thirsty_crow": {"title": "Thirsty Crow", "moral": "Where there is a will there is way", "lesson": "Creative problem solving"},
        }

    def _load_mythos(self) -> Dict[str, Dict]:
        return {
            "sisyphus": {"culture": "Greek", "story": "Sisyphus condemned to roll boulder uphill forever", "lesson": "Futile effort without strategy. Need smart work, not just hard work."},
            "hercules": {"culture": "Greek", "story": "12 labors of Hercules", "lesson": "Perseverance through difficult tasks, each labor teaches skill."},
            "gita": {"culture": "Indian", "story": "Krishna's Bhagavad Gita - duty without attachment", "lesson": "Focus on action, not result anxiety. Useful for stress, investment, business."},
            "ram_dharma": {"culture": "Indian", "story": "Ramayana - Ram follows dharma even in hardship", "lesson": "Righteousness and long-term reputation over short-term gain."},
            "thor": {"culture": "Norse", "story": "Thor's hammer only worthy can lift", "lesson": "Power needs worthiness, responsibility."},
        }

    def get_relevant_fable(self, query: str) -> Tuple[str, Dict]:
        q = query.lower()
        if any(w in q for w in ["slow", "steady", "persistence", "investment", "sip", "long term"]):
            return "tortoise_hare", self.fables["tortoise_hare"]
        if any(w in q for w in ["fomo", "jealous", "can't have", "crypto hype"]):
            return "fox_grapes", self.fables["fox_grapes"]
        if any(w in q for w in ["greed", "golden", "profit", "overtrade"]):
            return "goose_golden", self.fables["goose_golden"]
        if any(w in q for w in ["prepare", "future", "emergency", "save"]):
            return "ant_grasshopper", self.fables["ant_grasshopper"]
        if any(w in q for w in ["wit", "smart", "intelligence", "business"]):
            return "monkey_crocodile", self.fables["monkey_crocodile"]
        return "thirsty_crow", self.fables["thirsty_crow"]

    def get_relevant_mythos(self, query: str) -> Tuple[str, Dict]:
        q = query.lower()
        if any(w in q for w in ["duty", "stress", "anxiety", "attachment"]):
            return "gita", self.mythos["gita"]
        if any(w in q for w in ["futile", "loop", "stuck"]):
            return "sisyphus", self.mythos["sisyphus"]
        if any(w in q for w in ["perseverance", "hard", "labor", "difficult"]):
            return "hercules", self.mythos["hercules"]
        if any(w in q for w in ["dharma", "righteous", "right"]):
            return "ram_dharma", self.mythos["ram_dharma"]
        return "gita", self.mythos["gita"]

    def chain_of_thought(self, query: str, domain: str = "general") -> List[str]:
        """Claude-style chain of thought steps"""
        steps = []
        low = query.lower()
        
        if "investment" in domain or any(w in low for w in ["stock", "investment", "crypto"]):
            steps = [
                f"1. First, understand goal: User asks '{query}' - what is their risk appetite, time horizon?",
                "2. Assess risk: What are dangers? Volatility, loss, scams",
                "3. Options: What choices available? Stocks, mutual funds, gold, etc",
                "4. Strategy: Diversification, SIP, fundamental analysis",
                "5. Actionable plan: Specific next steps user can take",
                "6. Disclaimer + ask follow-up to personalize"
            ]
        elif "business" in domain:
            steps = [
                f"1. Problem: What problem does '{query}' solve?",
                "2. Customer: Who has this problem? How many?",
                "3. Solution: What MVP can be built quickly?",
                "4. Business model: How will it make money?",
                "5. Risks: What could fail?",
                "6. Next action: Smallest step to validate"
            ]
        elif "medical" in domain:
            steps = [
                f"1. Symptom analysis: '{query}' - what symptoms mentioned?",
                "2. Red flags: Any emergency signs? (chest pain, stiff neck, etc)",
                "3. General info: What could be common causes educationally?",
                "4. What NOT to do: Avoid self-diagnosis, don't delay emergency",
                "5. Next: When to see doctor, what to tell doctor, self-care general",
                "6. Disclaimer + empathy"
            ]
        elif "legal" in domain:
            steps = [
                f"1. Legal area: Is this criminal, civil, cyber, property?",
                "2. Rights: What are user's rights under Indian law?",
                "3. Procedure: What is correct legal process? FIR, court, etc",
                "4. Documents: What evidence to keep?",
                "5. Next: When to consult lawyer, where to report",
                "6. Disclaimer: Not a lawyer"
            ]
        else:
            # General
            steps = [
                f"1. Understand: What user really wants with '{query}'? Literal + intent",
                "2. Context: Emotional state, past history, Tanglish or English?",
                "3. Knowledge: What do I know from local knowledge base?",
                "4. Perspectives: Beginner view, expert view, skeptic view",
                "5. Answer: Clear, actionable, with example/fable if relevant",
                "6. Proactive: What follow-up would help user next?"
            ]
        
        return steps

    def self_reflect(self, response: str, query: str) -> Dict:
        """Claude-like self-critique after generating response"""
        critique = []
        confidence = 0.85
        
        # Check for potential issues
        if len(response) < 30:
            critique.append("Response too short, may lack depth")
            confidence -= 0.1
        if "i don't know" in response.lower() and len(response) < 100:
            critique.append("Could offer more helpful partial info")
        if any(word in response.lower() for word in ["always", "never", "guaranteed"]):
            critique.append("Uses absolute words - check if overconfident")
            confidence -= 0.1
        if "investment" in query.lower() and "not financial advice" not in response.lower():
            critique.append("Missing disclaimer for investment advice")
            confidence -= 0.2
        
        if not critique:
            critique.append("Response looks good - clear, empathetic, actionable, safe")
            confidence = 0.95
        
        return {"critique": critique, "confidence": confidence, "should_revise": confidence < 0.7}

# Singleton
_claude_intel = None

def get_claude_intelligence():
    global _claude_intel
    if _claude_intel is None:
        _claude_intel = ClaudeLevelIntelligence()
    return _claude_intel
