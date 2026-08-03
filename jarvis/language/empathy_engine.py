"""
JARVIS Empathy Engine - Understand human feelings like human
"""
import re
from typing import Dict, Tuple
from .human_personality import detect_emotion

class EmpathyEngine:
    def __init__(self):
        self.empathy_responses = {
            "stressed": {
                "en": "I can sense you're feeling stressed, Sir. It's completely normal. Let's tackle this together step by step. Take a deep breath first.",
                "ta-en": "Puriyudhu Sir, romba stress ah irukku nu theriyudhu. Paravala, normal dhan. Konjam deep breath edunga, naan kooda irukken. Onnathukku onnu solve pannalam."
            },
            "sad": {
                "en": "I'm here for you, Sir. It's okay to feel down sometimes. You don't have to carry this alone. Want to talk about it?",
                "ta-en": "Sir, naan irukken unga kooda. Sad ah irukka bothu pesuna konjam better ah feel pannuvom. Enna nadandhuchu sollunga."
            },
            "happy": {
                "en": "That's wonderful to hear, Sir! Your happiness is contagious. Let's celebrate this moment!",
                "ta-en": "Super Sir! Sandosha news kettu enakkum sandosham! Continue this energy!"
            },
            "angry": {
                "en": "I understand you're feeling frustrated, Sir. Take a moment, breathe. Let's figure out what we can do to fix this.",
                "ta-en": "Kovam varudhu nu puriyudhu Sir. Konjam time eduthukonga, cool pannunga. Eppadi fix pannalam nu paakalam."
            },
            "anxious": {
                "en": "I hear you're feeling anxious, Sir. That's valid. Let's break this down into smaller pieces. What's the biggest worry right now?",
                "ta-en": "Bayam/kalakkam irukku nu theriyudhu Sir. Paravala, ellarkum varum. Periya problem-a chinna pieces ah split panni paakalam."
            },
            "confused": {
                "en": "It's okay to feel confused, Sir. This is complex. Let me explain it in simple steps, and we'll clear this together.",
                "ta-en": "Kuzhappam irukku nu puriyudhu Sir. Complex vishayam dhan. Simple ah step by step explain panren, clear aagum."
            },
            "motivated": {
                "en": "I love your motivation, Sir! That fire is exactly what gets things done. Let's channel this energy into action!",
                "ta-en": "Semma motivation Sir! Indha energy dhan success ku mukkiyam. Ippo action ku poralam!"
            }
        }
    
    def analyze(self, text: str) -> Dict:
        emotion = detect_emotion(text)
        # Sentiment intensity (0-1)
        intensity = 0.5
        if any(w in text.lower() for w in ["romba", "very", "extremely", "too much"]):
            intensity = 0.9
        elif any(w in text.lower() for w in ["konjam", "little", "slightly"]):
            intensity = 0.3
        
        return {
            "emotion": emotion,
            "intensity": intensity,
            "is_vulnerable": emotion in ("sad", "stressed", "anxious"),
            "needs_empathy": emotion != "neutral",
            "language_hint": "ta-en" if any(w in text.lower() for w in ["pannu", "irukku", "enna", "romba"]) else "en"
        }
    
    def get_empathetic_opening(self, analysis: Dict) -> str:
        emotion = analysis.get("emotion", "neutral")
        lang = analysis.get("language_hint", "en")
        
        if emotion == "neutral":
            return ""
        
        return self.empathy_responses.get(emotion, {}).get(lang, self.empathy_responses.get(emotion, {}).get("en", ""))

    def enhance_response(self, original_response: str, analysis: Dict, domain: str = None) -> str:
        """Add empathy layer to response"""
        if not analysis.get("needs_empathy"):
            return original_response
        
        empathy_opening = self.get_empathetic_opening(analysis)
        if not empathy_opening:
            return original_response
        
        # For vulnerable emotions, prepend empathy, then solution
        if analysis.get("is_vulnerable"):
            return f"{empathy_opening}\n\n{original_response}"
        
        # For other emotions, add encouragement
        if analysis.get("emotion") == "happy":
            return f"{empathy_opening} {original_response}"
        
        return original_response

# Singleton
_empathy_engine = None

def get_empathy_engine():
    global _empathy_engine
    if _empathy_engine is None:
        _empathy_engine = EmpathyEngine()
    return _empathy_engine
