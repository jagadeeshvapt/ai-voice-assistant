"""
Base Skill class and registry
"""
import re
from typing import List, Dict, Callable, Optional, Tuple

class Skill:
    name: str = "base"
    description: str = "Base skill"
    # List of keywords/triggers
    keywords: List[str] = []
    # List of regex patterns
    patterns: List[str] = []

    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def can_handle(self, text: str) -> bool:
        text_low = text.lower()
        if any(kw in text_low for kw in self.keywords):
            return True
        for pat in self.compiled_patterns:
            if pat.search(text):
                return True
        return False

    def handle(self, text: str, context: Dict = None) -> Optional[str]:
        """Override in subclasses. Return response string or None"""
        raise NotImplementedError

    def get_match_score(self, text: str) -> int:
        """Score for intent matching - higher is better"""
        score = 0
        text_low = text.lower()
        for kw in self.keywords:
            if kw in text_low:
                score += 1
        for pat in self.compiled_patterns:
            if pat.search(text):
                score += 3
        return score


# Global skill registry
SKILL_REGISTRY: List[Skill] = []

def register_skill(cls):
    """Decorator to register skill"""
    instance = cls()
    SKILL_REGISTRY.append(instance)
    return cls

def get_best_skill(text: str) -> Tuple[Optional[Skill], int]:
    best = None
    best_score = 0
    for skill in SKILL_REGISTRY:
        score = skill.get_match_score(text)
        if score > best_score:
            best_score = score
            best = skill
    return best, best_score

def list_skills():
    return [(s.name, s.description) for s in SKILL_REGISTRY]
