import re
import datetime
import requests

from .base import Skill, register_skill
from ..config import config
from ..utils import logger

@register_skill
class WeatherSkill(Skill):
    name = "weather"
    description = "Weather information via OpenWeatherMap or wttr.in fallback"
    keywords = ["weather", "temperature", "forecast", "is it raining", "humidity", "wind", "climate", "hot", "cold", "weather today"]
    patterns = [
        r"weather (?:in |for |at )?(.+)?",
        r"temperature (?:in |at )?(.+)?",
        r"forecast (?:for )?(.+)?",
    ]

    def handle(self, text, context=None):
        low = text.lower()
        # Extract city
        city = config.DEFAULT_CITY
        m = re.search(r"weather (?:in |for |at )?(.+)", low)
        if m:
            possible_city = m.group(1).strip()
            # clean up common words
            possible_city = re.sub(r"\b(today|tomorrow|now|currently|like|outside)\b", "", possible_city).strip()
            if possible_city and len(possible_city) > 1 and len(possible_city) < 30:
                city = possible_city

        m2 = re.search(r"temperature (?:in |at )?(.+)", low)
        if m2:
            possible_city = m2.group(1).strip()
            possible_city = re.sub(r"\b(today|tomorrow|now|currently|like|outside)\b", "", possible_city).strip()
            if possible_city:
                city = possible_city

        # Try OpenWeatherMap first
        if config.OPENWEATHER_API_KEY:
            result = self._get_openweather(city)
            if result:
                return result
        
        # Fallback to wttr.in (no api key needed)
        return self._get_wttr(city)

    def _get_openweather(self, city: str):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.OPENWEATHER_API_KEY}&units=metric"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                logger.warning(f"OpenWeather error {r.status_code}: {r.text}")
                return None
            data = r.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            humidity = data['main']['humidity']
            wind = data['wind']['speed']
            return f"Weather in {city.title()}: {desc}, {temp}°C, humidity {humidity}%, wind {wind} m/s, sir"
        except Exception as e:
            logger.error(f"OpenWeather fetch failed: {e}")
            return None

    def _get_wttr(self, city: str):
        try:
            # wttr.in returns text
            url = f"https://wttr.in/{city}?format=%C+%t+%w+%h"
            r = requests.get(url, timeout=10, headers={'User-Agent': 'curl/7.64.1'})
            if r.status_code == 200 and r.text:
                # Example: Partly cloudy +22°C ...
                text = r.text.strip()
                return f"Weather in {city.title()}: {text}, sir"
            
            # JSON format fallback
            url2 = f"https://wttr.in/{city}?format=j1"
            r2 = requests.get(url2, timeout=10)
            if r2.status_code == 200:
                data = r2.json()
                current = data.get('current_condition', [{}])[0]
                temp = current.get('temp_C', 'N/A')
                desc = current.get('weatherDesc', [{}])[0].get('value', '')
                humidity = current.get('humidity', '')
                return f"Weather in {city.title()}: {desc}, {temp}°C, humidity {humidity}%"
        except Exception as e:
            logger.error(f"wttr.in fetch failed: {e}")
        
        return f"Couldn't fetch weather for {city}, please check your internet or configure OpenWeather API key"
