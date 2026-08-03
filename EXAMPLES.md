# JARVIS Examples - A to Z Usage

## Text Mode Session Example

```
$ python main.py --text

     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ...

[18:42:18] JARVIS: Good evening, Sir. It's 06:42 PM on Friday, July 18. How can I assist you today?

[Sir - Type] You: what time is it
[18:42:20] JARVIS: It's 06:42 PM Friday, sir

[Sir - Type] You: my name is Tony Stark
[18:42:22] JARVIS: Nice to meet you, Tony Stark. I'll remember that, sir.

[Sir - Type] You: add todo build iron man suit
[18:42:25] JARVIS: Added to todo: build iron man suit

[Sir - Type] You: weather in New York
[18:42:28] JARVIS: Weather in New York: Partly Cloudy +22°C, sir

[Sir - Type] You: calculate 45 * 8
[18:42:30] JARVIS: The answer is 360, sir

[Sir - Type] You: play Believer on YouTube
[18:42:33] JARVIS: Searching YouTube for Believer, sir. Opening browser.

[Sir - Type] You: tell me a joke
[18:42:35] JARVIS: Why do programmers prefer dark mode? Because light attracts bugs!

[Sir - Type] You: remind me to call Pepper in 10 minutes
[18:42:38] JARVIS: Reminder set: call Pepper at 2026-07-31 18:52, sir

[Sir - Type] You: exit
[18:42:40] JARVIS: Going offline, sir. Call me if you need anything.
```

## Voice Mode

```
$ python main.py

[JARVIS] Listening for wake word: ['jarvis', 'hey jarvis', 'ok jarvis'] ...

You say: "Jarvis what time is it"
JARVIS: "It's 6:42 PM Friday, sir"

You say: "Hey Jarvis open GitHub"
JARVIS: "Opening github, sir" -> opens browser

You say: "Jarvis shutdown"
JARVIS: "Initiating shutdown sequence..." (10 sec timer)
```

## Single Command

```bash
python main.py --single "what time is it"
python main.py --single "open youtube"
python main.py --single "tell me a joke"
python main.py --single "search for quantum computing"
```

## GUI

```bash
python main.py --gui
```
- Arc reactor animates
- Type in bottom bar or click "START LISTENING" for voice
- Quick action buttons

## API Server

```bash
python server.py
# Server at http://localhost:8000
# Docs at http://localhost:8000/docs

curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"query": "what time is it"}'

# WebSocket JS example:
const ws = new WebSocket("ws://localhost:8000/ws")
ws.onmessage = (e) => console.log(JSON.parse(e.data))
ws.onopen = () => ws.send("hello jarvis")
```

## With OpenAI (Super Smart)

```ini
# .env
OPENAI_API_KEY=sk-proj-....
OPENAI_MODEL=gpt-4o-mini
```

Then JARVIS understands natural language like:
- "Jarvis can you summarize what I asked today?"
- "Jarvis I'm bored, entertain me"
- "Jarvis write a Python function to sort a list and save it to file"

Because GPT brain + skill tool execution.

## Extending Skills

Add `jarvis/skills/news.py`:

```python
from .base import Skill, register_skill
import requests

@register_skill
class NewsSkill(Skill):
    name = "news"
    description = "Latest news"
    keywords = ["news", "headlines"]
    def handle(self, text, context=None):
        if "news" in text.lower():
            # fetch news API
            return "Top headline: ..."
```

And add `from . import news` in `jarvis/skills/__init__.py`.

Restart JARVIS and say "latest news".

## Deployment

```bash
docker build -t jarvis .
docker run -p 8000:8000 jarvis
```
