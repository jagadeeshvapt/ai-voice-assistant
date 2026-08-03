"""
Utility functions
"""
import re
import logging
import datetime
import platform
import subprocess
import webbrowser
import sys
from pathlib import Path

from .config import config

# Logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("JARVIS")

def clean_text(text: str) -> str:
    """Normalize text for processing"""
    return re.sub(r'\s+', ' ', text.strip().lower())

def extract_number(text: str):
    m = re.search(r'\d+', text)
    return int(m.group()) if m else None

def get_system_info() -> str:
    return f"{platform.system()} {platform.release()} on {platform.machine()}"

def open_url(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}"

def run_command(cmd: str):
    try:
        if platform.system() == "Windows":
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(cmd, shell=True)
        return True
    except Exception as e:
        logger.error(f"run_command failed: {e}")
        return False

def speak_print(text: str):
    """Log assistant response"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {config.JARVIS_NAME}: {text}")
    logger.info(f"ASSISTANT: {text}")

def user_print(text: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {config.USER_NAME}: {text}")
    logger.info(f"USER: {text}")

def remove_wake_word(text: str) -> str:
    lower = text.lower()
    for wake in config.WAKE_WORDS:
        if wake in lower:
            lower = lower.replace(wake, "").strip()
    return lower.strip()

def get_greeting():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 21:
        return "Good evening"
    else:
        return "Hello"

def is_url(text: str) -> bool:
    return bool(re.search(r'(https?://|www\.|\.com|\.org|\.net)', text.lower()))
