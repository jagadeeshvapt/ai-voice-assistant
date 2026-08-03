import re
import webbrowser
import random

from .base import Skill, register_skill
from ..config import config
from ..utils import logger

@register_skill
class MediaSkill(Skill):
    name = "media"
    description = "Plays YouTube, music, jokes, stories"
    keywords = [
        "play", "youtube", "music", "song", "video", "pause", "resume", "stop music",
        "joke", "funny", "make me laugh", "tell me a joke", "story", "entertain"
    ]
    patterns = [
        r"play (.+) on youtube",
        r"play (.+) youtube",
        r"play (?:the )?(?:song )?(?:music )?(.+)",
        r"youtube (.+)",
        r"search youtube (.+)",
        r"tell (?:me )?(?:a )?joke",
        r"play music",
    ]

    def handle(self, text, context=None):
        low = text.lower()

        # Jokes
        if "joke" in low or "funny" in low or "make me laugh" in low:
            try:
                import pyjokes
                joke = pyjokes.get_joke(language='en', category='all')
                return joke
            except:
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "I told my computer I needed a break, and now it won't stop sending me vacation ads.",
                    "Why did the AI go to therapy? It had too many deep learning issues.",
                    "Siri and I used to date, but she kept saying: I don't understand that."
                ]
                return random.choice(jokes)

        # Music controls
        if any(x in low for x in ["pause music", "pause song", "pause video"]):
            try:
                import pyautogui
                pyautogui.press('playpause')
                return "Music paused"
            except:
                return "Pausing media"

        if any(x in low for x in ["resume", "continue music", "play music"] ) and len(low.split()) <= 3:
            try:
                import pyautogui
                pyautogui.press('playpause')
                return "Resuming, sir"
            except:
                return "Resuming"

        if "stop music" in low or "stop song" in low:
            try:
                import pyautogui
                pyautogui.press('stop')
                return "Stopped"
            except:
                return "Stopping music"

        # YouTube play
        youtube_query = None
        m = re.search(r"play (.+) on youtube", low)
        if m:
            youtube_query = m.group(1).strip()
        else:
            m = re.search(r"play (.+) youtube", low)
            if m:
                youtube_query = m.group(1).strip()
            else:
                m = re.search(r"youtube (.+)", low)
                if m and "search" in low:
                    youtube_query = m.group(1).strip()
                elif "play" in low:
                    m = re.search(r"play (?:the )?(?:song )?(?:music )?(.+)", low)
                    if m:
                        youtube_query = m.group(1).strip()
                        # Avoid generic "play music"
                        if youtube_query.lower() in ("music", "song", "some music", "a song"):
                            youtube_query = None
                            # Open YouTube Music
                            webbrowser.open("https://music.youtube.com")
                            return "Opening YouTube Music, sir"

        if youtube_query:
            # Clean query
            youtube_query = youtube_query.replace("play ", "").strip()
            if len(youtube_query) < 1:
                return None
            
            # Try to use pytube search? Simplified to open YouTube search
            from urllib.parse import quote
            url = f"https://www.youtube.com/results?search_query={quote(youtube_query)}"
            webbrowser.open(url)
            
            # Attempt first result auto-play via YouTube? Open first result heuristic
            # For simplicity, open search - more reliable than scraping
            return f"Searching YouTube for {youtube_query}, sir. Opening browser."

        if "play music" == low.strip() or low.strip() == "play song":
            webbrowser.open("https://music.youtube.com")
            return "Opening YouTube Music, sir"

        return None
