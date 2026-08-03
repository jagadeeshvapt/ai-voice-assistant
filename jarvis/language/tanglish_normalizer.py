"""
JARVIS Language - Tanglish Normalizer
Handles English, Tamil script, Tanglish mixed

Examples:
"Chrome open panni YouTube launch pannu" -> normalized intent
"volume konjam kammi pannu" -> volume decrease
"light off pannidu" -> light off
"enna time?" -> what time

Converts informal Tanglish to standard form for intent parsing
"""
import re
import unicodedata
from typing import Dict, Tuple, List

class TanglishNormalizer:
    def __init__(self):
        # Synonym dictionary for Tanglish -> English normalized
        self.synonyms = {
            # Actions - Tanglish verbs
            "open pannu": "open",
            "open panni": "open",
            "open pannidu": "open",
            "open pannunga": "open",
            "open panniten": "opened",
            "open pannuren": "opening",
            "close pannu": "close",
            "close panni": "close",
            "launch pannu": "open",
            "start pannu": "open",
            "podus": "set",
            "podu": "set",
            "podu da": "set",
            "pannu": "do",
            "panni": "do",
            "pannidu": "do",
            "pannunga": "do",
            "vaika": "set",
            "vai": "set",
            "vechu": "set",
            
            # Volume
            "kammi pannu": "decrease",
            "kammi panni": "decrease",
            "kura": "decrease",
            "kuraivu": "decrease",
            "konjam kammi": "decrease a little",
            "increase pannu": "increase",
            "kuda pannu": "increase",
            "jaasti pannu": "increase",
            "athi ha pannu": "increase",
            "satham": "volume",
            "sounda": "volume",
            "volume ah": "volume",
            
            # Common Tamil words in Tanglish
            "enna": "what",
            "epdi": "how",
            "enga": "where",
            "eppo": "when",
            "yaar": "who",
            "edhu": "what",
            "enakku": "for me",
            "unakku": "for you",
            "innaiku": "today",
            "naalaikku": "tomorrow",
            "nerthikku": "yesterday",
            "ippo": "now",
            "aprom": "later",
            "konjam": "a little",
            "romba": "very",
            "illa": "no",
            "aama": "yes",
            "sari": "okay",
            "seri": "okay",
            "paravala": "okay",
            "mudiyala": "cannot",
            "mudiyum": "can",
            "venum": "want",
            "venda": "dont want",
            "pannalama": "shall we do",
            "podava": "shall i set",
            "irukku": "there is",
            "illaya": "is there not",
            "edhavadhu": "something",
            "onnum illa": "nothing",
            
            # Time related
            "maniku": "o'clock",
            "manikku": "o'clock",
            "kaalai": "morning",
            "maalai": "evening",
            "madhyam": "afternoon",
            "iravu": "night",
            "naalaiku": "tomorrow",
            
            # Adhula, indha, etc - contextual
            "adhula": "in it",
            "idula": "in this",
            "andha": "that",
            "indha": "this",
            "edhula": "in which",
            
            # Light, system
            "off pannu": "turn off",
            "on pannu": "turn on",
            "light ah": "light",
            "fan ah": "fan",
            "ac ah": "ac",
        }
        
        # Tamil script to transliterated mapping for common words (partial)
        self.tamil_script_map = {
            "ஜார்விஸ்": "jarvis",
            "என்ன": "enna",
            "நேரம்": "time",
            "குரோம்": "chrome",
            "திற": "open",
            "மூடு": "close",
            "ஒலி": "volume",
        }
        
        # Compile patterns for faster replacement - longest first
        self.sorted_keys = sorted(self.synonyms.keys(), key=len, reverse=True)

    def detect_language(self, text: str) -> str:
        """Detect if text is en, ta, or tanglish (ta-en)"""
        has_tamil_unicode = any('\u0B80' <= c <= '\u0BFF' for c in text)
        has_ascii = any(c.isascii() and c.isalpha() for c in text)
        
        if has_tamil_unicode and has_ascii:
            return "ta-en"
        elif has_tamil_unicode:
            return "ta"
        else:
            # Check for tanglish markers
            tanglish_markers = ["pannu", "panni", "da", "di", "enna", "konjam", "romba", "illa", "irukku", "venum", "manikku", "podu"]
            low = text.lower()
            if any(m in low for m in tanglish_markers):
                return "ta-en"
            return "en"

    def transliterate_tamil_script(self, text: str) -> str:
        """Basic Tamil script -> tanglish transliteration"""
        result = text
        for ta, en in self.tamil_script_map.items():
            result = result.replace(ta, en)
        
        # For remaining Tamil unicode, keep as is but also attempt to normalize
        # In production, use ai4bharat transliteration, here simple pass
        return result

    def normalize(self, text: str) -> Tuple[str, Dict]:
        """
        Normalize Tanglish text to English-ish form for intent parsing
        Returns (normalized_text, meta)
        """
        original = text
        lang = self.detect_language(text)
        
        # Step 1: If Tamil script, transliterate
        if lang in ("ta", "ta-en"):
            text = self.transliterate_tamil_script(text)
        
        low = text.lower()
        
        # Step 2: Replace synonyms - longest match first
        normalized = low
        replacements = []
        for key in self.sorted_keys:
            if key in normalized:
                repl = self.synonyms[key]
                # Use word boundaries where possible but Tanglish often without
                normalized = normalized.replace(key, repl)
                replacements.append((key, repl))
        
        # Step 3: Clean up extra spaces, handle common patterns
        # "Chrome open pannu" -> "open Chrome" (verb position)
        # Handle "X open" -> "open X" (important for Tamil word order)
        # e.g., "chrome open" -> "open chrome", "notepad open pannu" -> "open notepad"
        m = re.search(r"^(.+?)\s+open$", normalized.strip())
        if m:
            app_part = m.group(1).strip()
            # Don't convert if app_part is empty or is a verb like "volume", etc
            if app_part and len(app_part.split()) <= 4:
                normalized = f"open {app_part}"
        
        # Also handle "X open panni" type still
        m2 = re.search(r"^(.+?)\s+open\s+(?:panni|pannu|pannitu)$", normalized)
        if m2:
            normalized = f"open {m2.group(1).strip()}"
        
        # "volume 40-ku set pannu" -> "set volume 40 percent"
        normalized = re.sub(r"(\d+)\s*(-ku|ku|%|percent)?\s*set", r"set \1 percent", normalized)
        normalized = re.sub(r"volume\s+(\d+)", r"set volume \1", normalized)
        
        # "6 manikku" -> "at 6 o'clock"
        normalized = re.sub(r"(\d+)\s*maniku?", r"at \1 o'clock", normalized, flags=re.IGNORECASE)
        
        # "naalaikku kaalai 7 manikku" -> "tomorrow morning at 7"
        normalized = normalized.replace("naalaikku", "tomorrow").replace("kaalai", "morning").replace("maalai", "evening")
        
        # Remove filler words that don't help intent
        fillers = ["da", "di", "nga", "pa", "la", "ku", "ah", "tha", "dhaan"]
        words = normalized.split()
        filtered = [w for w in words if w not in fillers]
        normalized = " ".join(filtered)
        
        # Final cleanup
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        meta = {
            "language": lang,
            "original": original,
            "replacements": replacements,
            "is_tanglish": lang == "ta-en",
            "confidence": 0.9 if lang in ("en", "ta-en") else 0.7
        }
        
        return normalized, meta

    def denormalize_response(self, english_response: str, target_language: str) -> str:
        """Convert English response to Tanglish if needed"""
        if target_language == "en":
            return english_response
        
        if target_language == "ta-en":
            # Simple conversion: add Tanglish endings
            conversions = {
                "opened": "open panniten",
                "opening": "open pannuren",
                "closed": "close panniten",
                "decreased": "kammi panniten",
                "increased": "jaasthi panniten",
                "set": "set panniten",
                "done": "mudichiten",
                "cannot": "mudiyala",
                "there is": "irukku",
                "okay": "sari",
            }
            result = english_response
            # Only apply to short responses for naturalness
            if len(result.split()) < 12:
                for en, ta in conversions.items():
                    result = result.replace(en, ta)
            return result
        
        return english_response

# Singleton
_normalizer = None

def get_normalizer() -> TanglishNormalizer:
    global _normalizer
    if _normalizer is None:
        _normalizer = TanglishNormalizer()
    return _normalizer
