import re
import requests
from urllib.parse import quote
from .base import Skill, register_skill
from ..utils import logger

# Try to import duckduckgo search
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

@register_skill
class WebSearchSkill(Skill):
    name = "web_search"
    description = "Searches the web, opens URLs, googles"
    keywords = ["search", "google", "look up", "find", "browse", "open website", "youtube search", "on youtube", "search web"]
    patterns = [
        r"search (?:for )?(.+)",
        r"google (.+)",
        r"look up (.+)",
        r"find (.+) on (google|youtube|web)",
        r"open (https?://\S+|www\.\S+|\S+\.com\S*)",
        r"browse (.+)",
    ]

    def handle(self, text, context=None):
        low = text.lower()

        # Direct URL opening
        url_match = re.search(r"(https?://\S+|www\.\S+|\S+\.com\S*)", text)
        if "open" in low and url_match:
            url = url_match.group(1)
            if not url.startswith("http"):
                url = "https://" + url
            import webbrowser
            webbrowser.open(url)
            return f"Opening {url}, sir"

        # YouTube search specially handled? delegated to media skill, but we handle fallback
        if "youtube" in low and ("search" in low or "play" in low):
            return None  # Let media skill handle

        # General search
        query = None
        patterns = [
            r"search (?:for )?(.+)",
            r"google (.+)",
            r"look up (.+)",
            r"browse (.+)"
        ]
        for pat in patterns:
            m = re.search(pat, low)
            if m:
                query = m.group(1).strip()
                # Remove trailing "on google" etc
                query = re.sub(r"\s+on\s+(google|youtube|web|internet)$", "", query)
                break

        if not query and any(k in low for k in ["search", "google", "look up", "browse", "find"]):
            # Use whole text minus keywords as query
            query = re.sub(r"(search|google|look up|browse|find|for|on web|on google)", "", low).strip()

        if not query or len(query) < 2:
            return None

        # Try DDGS
        if DDGS_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=3))
                    if results:
                        summary = results[0].get('body', '')[:400]
                        link = results[0].get('href', '')
                        # Open top result
                        # import webbrowser
                        # webbrowser.open(link)
                        return f"Here's what I found for {query}: {summary}. Source: {results[0].get('title')}"
            except Exception as e:
                logger.warning(f"DDGS search failed: {e}")

        # Fallback: open google search
        try:
            import webbrowser
            url = f"https://www.google.com/search?q={quote(query)}"
            webbrowser.open(url)
            return f"Searching Google for {query}, sir. Opening browser."
        except Exception as e:
            return f"Search failed: {e}"

    def quick_answer(self, query: str) -> str:
        """Try to get quick answer without opening browser"""
        if not DDGS_AVAILABLE:
            return ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=1))
                if results:
                    return results[0].get('body', '')[:500]
        except:
            pass
        return ""
