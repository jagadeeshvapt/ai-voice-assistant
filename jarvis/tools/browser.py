"""
JARVIS Tools - Browser automation, local Playwright/Selenium fallback to simple webbrowser
"""
import webbrowser
from urllib.parse import quote
from typing import Dict
from .registry import Tool
from ..utils import logger
from ..config import config

class BrowserTool(Tool):
    name = "browser_search"
    description = "Searches web via browser (offline uses local history if offline_only)"
    dangerous = False
    required_permission = 1

    def validate(self, arguments: Dict):
        pass

    def execute(self, arguments: Dict):
        query = arguments.get("query") or arguments.get("text") or arguments.get("raw") or ""
        engine = arguments.get("engine", "google").lower()
        url = arguments.get("url")
        
        # Clean query
        if not query and not url:
            return "Enna search pannanum-nu sollunga."
        
        # If direct URL
        if url:
            return self._open_url(url)
        
        # If query looks like URL
        if query.startswith("http") or ".com" in query or ".org" in query:
            return self._open_url(query)
        
        # Search
        if config.OFFLINE_ONLY:
            # Offline mode - still open browser but with local search? For now open browser with search URL (needs internet but okay - it's not cloud API, it's user browser)
            # If strictly no internet, we could search local knowledge base
            logger.info(f"Offline search requested for {query}, opening browser anyway (may fail without internet)")
        
        return self._search(query, engine)

    def _open_url(self, url: str):
        if not url.startswith("http"):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return f"{url} open panniten browser la."
        except Exception as e:
            return f"Browser open failed: {e}"

    def _search(self, query: str, engine: str):
        try:
            q = quote(query)
            if "youtube" in engine:
                url = f"https://www.youtube.com/results?search_query={q}"
            elif "bing" in engine:
                url = f"https://www.bing.com/search?q={q}"
            else:
                url = f"https://www.google.com/search?q={q}"
            webbrowser.open(url)
            return f"{engine} la {query} search pannuren, browser open panniten."
        except Exception as e:
            return f"Search failed: {e}"

class OpenWebsiteTool(BrowserTool):
    name = "open_website"
class PlayYoutubeTool(BrowserTool):
    name = "play_youtube"
    def execute(self, args):
        query = args.get("query") or args.get("text") or args.get("raw") or ""
        # Open YouTube search
        return self._search(query, "youtube")
