import re
import wikipedia
import requests

from .base import Skill, register_skill
from ..utils import logger

@register_skill
class KnowledgeSkill(Skill):
    name = "knowledge"
    description = "Answers questions using Wikipedia and general knowledge"
    keywords = [
        "who is", "what is", "what are", "define", "explain", "tell me about", "wikipedia",
        "meaning", "information", "knowledge", "describe", "history of", "what does"
    ]
    patterns = [
        r"who is (.+)",
        r"what is (.+)",
        r"what are (.+)",
        r"tell me about (.+)",
        r"search wikipedia (?:for )?(.+)",
        r"wikipedia (.+)",
        r"define (.+)",
        r"explain (.+)",
        r"history of (.+)"
    ]

    def handle(self, text, context=None):
        low = text.lower().strip()

        # Try to extract topic
        topic = None
        patterns = [
            r"who is (.+)",
            r"what is (.+)",
            r"what are (.+)",
            r"tell me about (.+)",
            r"search wikipedia (?:for )?(.+)",
            r"wikipedia (.+)",
            r"define (.+)",
            r"explain (.+)",
            r"history of (.+)"
        ]
        for pat in patterns:
            m = re.search(pat, low)
            if m:
                topic = m.group(1).strip()
                # Remove question mark and "jarvis" leftover
                topic = topic.replace("?", "").replace(" jarvis", "").strip()
                break

        if not topic:
            # Maybe it's a general question with those keywords
            for kw in ["who is", "what is", "what are", "tell me about", "define", "explain"]:
                if kw in low:
                    topic = low.split(kw)[-1].strip().replace("?", "")
                    break

        if not topic or len(topic) < 2 or len(topic) > 100:
            return None

        # Avoid answering simple conversions that should go elsewhere
        if len(topic.split()) > 10:
            return None

        # Try Wikipedia
        try:
            # Set auto suggest false for more precise
            summary = wikipedia.summary(topic, sentences=2, auto_suggest=False)
            if summary:
                return f"According to Wikipedia about {topic}: {summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                # Pick first option
                option = e.options[0]
                summary = wikipedia.summary(option, sentences=2)
                return f"{topic} may refer to many things. Here's about {option}: {summary}"
            except:
                pass
        except wikipedia.exceptions.PageError:
            pass
        except Exception as e:
            logger.debug(f"Wikipedia error for '{topic}': {e}")

        # Try DuckDuckGo instant answer as fallback
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(topic, max_results=2))
                if results:
                    body = results[0].get('body', '')[:600]
                    if body:
                        return f"Here's what I found about {topic}: {body}"
        except Exception as e:
            logger.debug(f"DDGS fallback failed: {e}")

        return None
