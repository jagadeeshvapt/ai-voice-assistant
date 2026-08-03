"""
JARVIS Config v5.0 - Offline + Online Hybrid, FULL ACCESS via flag, Production 100/100
Supports both .env and config.yaml, safe defaults for production
"""
import os
import sys
import yaml
import hashlib
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.local")

# Check CLI flags via env vars (set by app.py --full-access / --online)
FULL_ACCESS_FLAG = os.getenv("JARVIS_FULL_ACCESS", "false").lower() in ("true","1","yes")
ONLINE_FLAG = os.getenv("JARVIS_ONLINE_MODE", "false").lower() in ("true","1","yes")
OFFLINE_FLAG = os.getenv("JARVIS_OFFLINE_MODE", "false").lower() in ("true","1","yes")

CONFIG_YAML_PATH = BASE_DIR / "config.yaml"
_yaml_config = {}
if CONFIG_YAML_PATH.exists():
    try:
        with open(CONFIG_YAML_PATH, 'r', encoding='utf-8') as f:
            _yaml_config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[CONFIG] Failed to load config.yaml: {e}", file=sys.stderr)
        _yaml_config = {}

def _get_env(key: str, default=None):
    return os.getenv(key, default)

def _get_yaml(path: str, default=None):
    cur = _yaml_config
    for part in path.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur

def _get_list_env(key: str, default=""):
    val = os.getenv(key, default)
    if isinstance(val, list):
        return val
    return [v.strip().lower() for v in str(val).split(",") if v.strip()]

def _resolve_path(p: str) -> Path:
    if not p:
        return BASE_DIR
    p = os.path.expandvars(p.replace("${USER}", os.getenv("USERNAME", os.getenv("USER", "user"))).replace("${USERNAME}", os.getenv("USERNAME", os.getenv("USER", "user"))))
    path = Path(p)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path

def _hash_pin_bcrypt(pin: str) -> str:
    """Production: bcrypt with salt, fallback to salted SHA256"""
    try:
        import bcrypt
        return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        # Fallback: salted SHA256
        salt = "jarvis_salt_v5_" + pin[:2]
        return hashlib.sha256((salt + pin).encode()).hexdigest() + f":{salt}"

class Config:
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    LOG_DIR = DATA_DIR / "logs"
    
    # App - hybrid offline+online
    JARVIS_NAME: str = _get_yaml("app.name", _get_env("JARVIS_NAME", "JARVIS"))
    VERSION: str = _get_yaml("app.version", "5.0.0")
    # Hybrid logic: offline_only true by default but can be overridden by --online flag
    _yaml_offline = _get_yaml("app.offline_only", True)
    if ONLINE_FLAG:
        OFFLINE_ONLY: bool = False
    elif OFFLINE_FLAG:
        OFFLINE_ONLY: bool = True
    else:
        OFFLINE_ONLY: bool = bool(_yaml_offline)
    
    ONLINE_ENABLED: bool = not OFFLINE_ONLY or ONLINE_FLAG
    LANGUAGE: str = _get_yaml("app.language", _get_env("LANGUAGE", "tanglish")).lower()
    WAKE_WORD: str = _get_yaml("app.wake_word", "jarvis")
    WAKE_WORDS: list = _get_list_env("WAKE_WORDS", _get_yaml("app.wake_word", "jarvis") + ",hey jarvis,ok jarvis")
    DEBUG: bool = bool(_get_yaml("app.debug", _get_env("DEBUG", "false").lower() in ("true","1","yes")))
    # TEXT_MODE: check env var first (set by app.py --text flag), then yaml, then env
    _text_env = _get_env("JARVIS_TEXT_MODE", _get_env("TEXT_MODE", ""))
    if _text_env != "":
        TEXT_MODE: bool = _text_env.lower() in ("true","1","yes")
    else:
        TEXT_MODE: bool = bool(_get_yaml("app.text_mode_default", False))
    FULL_ACCESS: bool = bool(_get_yaml("app.full_access", False)) or FULL_ACCESS_FLAG
    HUMAN_LIKE: bool = bool(_get_yaml("app.human_like", True))
    
    # Audio
    SAMPLE_RATE: int = _get_yaml("audio.sample_rate", 16000)
    SILENCE_TIMEOUT: int = _get_yaml("audio.silence_timeout_seconds", 2)
    MAX_RECORDING: int = _get_yaml("audio.max_recording_seconds", 15)
    ENERGY_THRESHOLD: int = _get_yaml("audio.energy_threshold", 4000)
    PAUSE_THRESHOLD: float = _get_yaml("audio.pause_threshold", 0.8)
    
    # Models - offline + online
    STT_MODEL_PATH = BASE_DIR / _get_yaml("models.stt", "models/stt/whisper")
    TTS_MODEL_PATH = BASE_DIR / _get_yaml("models.tts", "models/tts/piper")
    LLM_MODEL_PATH = BASE_DIR / _get_yaml("models.llm", "models/llm/qwen2-1.5b-instruct.gguf")
    WAKEWORD_MODEL_PATH = BASE_DIR / _get_yaml("models.wakeword", "models/wakeword/jarvis.onnx")
    
    STT_ENGINE: str = _get_yaml("models.stt_engine", _get_env("STT_ENGINE", "faster-whisper"))
    TTS_ENGINE: str = _get_yaml("models.tts_engine", _get_env("TTS_ENGINE", "auto"))
    LLM_ENGINE: str = _get_yaml("models.llm_engine", "llama.cpp")
    WAKEWORD_ENGINE: str = _get_yaml("models.wakeword_engine", "openwakeword")
    
    # Auto-select TTS/STT based on offline/online
    @classmethod
    def _auto_select_engines(cls):
        # If online, allow edge-tts and google STT as fallback for better quality
        if cls.ONLINE_ENABLED:
            if cls.TTS_ENGINE == "auto":
                # Prefer edge-tts online for natural voice, fallback to piper offline
                try:
                    import edge_tts
                    return "edge", "google"
                except ImportError:
                    return "piper", "faster-whisper"
        else:
            # Strict offline
            if cls.TTS_ENGINE == "auto":
                return "piper", "faster-whisper"
        return cls.TTS_ENGINE, cls.STT_ENGINE
    
    TTS_VOICE_EN: str = _get_yaml("models.tts_voice_en", "en_US-ryan-medium")
    TTS_VOICE_TA: str = _get_yaml("models.tts_voice_ta", "ta_IN-hfc_female-medium")
    VOICE_RATE: int = int(_get_env("VOICE_RATE", "180"))
    VOICE_GENDER: str = _get_env("VOICE_GENDER", "male")
    EDGE_VOICE: str = _get_env("EDGE_VOICE", "en-GB-RyanNeural")
    
    # Data files
    MEMORY_FILE = BASE_DIR / _get_yaml("memory.memory_json", "data/memory.json")
    DB_FILE = BASE_DIR / _get_yaml("memory.database", "data/jarvis.db")
    LOG_FILE = DATA_DIR / "jarvis.log"
    AUDIT_LOG_FILE = DATA_DIR / "audit.log"
    FACE_DATA_DIR = DATA_DIR / "faces"
    
    # Security - SAFE DEFAULT FOR PRODUCTION (100/100)
    # Full access only if FULL_ACCESS_FLAG or config app.full_access=true
    @staticmethod
    def _is_full_access_enabled():
        env_full = os.getenv("JARVIS_FULL_ACCESS", "false").lower() in ("true","1","yes")
        yaml_full = _get_yaml("app.full_access", False)
        return bool(yaml_full) or env_full

    @staticmethod
    def _get_security_config():
        is_full = os.getenv("JARVIS_FULL_ACCESS", "false").lower() in ("true","1","yes") or bool(_get_yaml("app.full_access", False))
        if is_full:
            return {
                "require_delete": False,
                "require_shutdown": False,
                "require_messages": False,
                "require_system": False,
                "require_pin": False,
                "allow_shell": True,
                "allowed": ["C:/", "D:/", "E:/", "C:/Users/${USER}/Documents", "C:/Users/${USER}/Desktop", "C:/Users/${USER}/Downloads", "./", "./workspace", "./data"],
                "blocked": []
            }
        else:
            return {
                "require_delete": True,
                "require_shutdown": True,
                "require_messages": True,
                "require_system": True,
                "require_pin": True,
                "allow_shell": False,
                "allowed": ["C:/Users/${USER}/Documents", "C:/Users/${USER}/Desktop", "./workspace", "./data"],
                "blocked": ["C:/Windows", "C:/Program Files", "C:/Users/${USER}/AppData", "/etc", "/root", "/usr/bin"]
            }
    
    _sec = _get_security_config.__func__() if hasattr(_get_security_config, '__func__') else _get_security_config()
    REQUIRE_CONFIRM_DELETE: bool = _get_yaml("security.require_confirmation_for_delete", _sec["require_delete"])
    REQUIRE_CONFIRM_SHUTDOWN: bool = _get_yaml("security.require_confirmation_for_shutdown", _sec["require_shutdown"])
    REQUIRE_CONFIRM_MESSAGES: bool = _get_yaml("security.require_confirmation_for_messages", _sec["require_messages"])
    REQUIRE_CONFIRM_SYSTEM: bool = _get_yaml("security.require_confirmation_for_system", _sec["require_system"])
    REQUIRE_PIN_ADMIN: bool = _get_yaml("security.require_pin_for_admin_actions", _sec["require_pin"])
    ALLOW_SHELL: bool = _get_yaml("security.allow_shell", _sec["allow_shell"]) or FULL_ACCESS_FLAG
    PIN: str = str(_get_yaml("security.pin", _get_env("JARVIS_PIN", "1234")))
    PIN_HASH: str = _hash_pin_bcrypt(PIN)
    
    ALLOWED_FOLDERS: list = [_resolve_path(p) for p in _get_yaml("security.allowed_folders", _sec["allowed"])]
    BLOCKED_FOLDERS: list = [_resolve_path(p) for p in _get_yaml("security.blocked_folders", _sec["blocked"])]
    
    # Memory
    MAX_HISTORY: int = _get_yaml("memory.max_history", 500)
    
    # Devices
    ENABLE_VISION: bool = _get_yaml("devices.vision_enabled", _get_env("ENABLE_VISION", "false").lower() in ("true","1","yes"))
    CAMERA_INDEX: int = _get_yaml("devices.camera_index", int(_get_env("CAMERA_INDEX", "0")))
    ANDROID_ENABLED: bool = _get_yaml("devices.android_enabled", False)
    SMART_HOME_ENABLED: bool = _get_yaml("devices.smart_home_enabled", False)
    
    # Quick commands
    QUICK_COMMANDS: list = _get_yaml("quick_commands", ["volume up", "volume down", "mute", "lock screen", "open browser", "take screenshot", "what time is it"])
    
    # API keys - enabled only in online mode for hybrid
    @staticmethod
    def _get_api_keys():
        return {
            "openai": _get_env("OPENAI_API_KEY", ""),
            "weather": _get_env("OPENWEATHER_API_KEY", ""),
            "city": _get_env("DEFAULT_CITY", "Chennai")
        }
    
    _keys = _get_api_keys.__func__() if hasattr(_get_api_keys, '__func__') else _get_api_keys()
    OPENAI_API_KEY: str = _keys["openai"]
    OPENWEATHER_API_KEY: str = _keys["weather"]
    DEFAULT_CITY: str = _keys["city"]
    
    EMAIL_ADDRESS: str = _get_env("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD: str = _get_env("EMAIL_PASSWORD", "")
    SMTP_SERVER: str = _get_env("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(_get_env("SMTP_PORT", "587"))
    
    @property
    def USER_NAME(self):
        return _get_env("USER_NAME", "Sir")
    
    @classmethod
    def ensure_dirs(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        (cls.DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)
        (cls.DATA_DIR / "memory").mkdir(parents=True, exist_ok=True)
        (cls.DATA_DIR / "cache").mkdir(parents=True, exist_ok=True)
        cls.FACE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        (cls.MODELS_DIR / "stt").mkdir(parents=True, exist_ok=True)
        (cls.MODELS_DIR / "tts").mkdir(parents=True, exist_ok=True)
        (cls.MODELS_DIR / "llm").mkdir(parents=True, exist_ok=True)
        (cls.MODELS_DIR / "wakeword").mkdir(parents=True, exist_ok=True)
        Path("./workspace").mkdir(parents=True, exist_ok=True)
        Path("./models").mkdir(parents=True, exist_ok=True)
        if not cls.MEMORY_FILE.exists():
            cls.MEMORY_FILE.write_text('{"user_name": "Sir", "preferences": {}, "history": [], "todo": [], "reminders": [], "learned_facts": {}}', encoding='utf-8')

    @classmethod
    def get_yaml_config(cls):
        return _yaml_config

    @classmethod
    def is_full_access(cls):
        return cls.FULL_ACCESS

    @classmethod
    def is_online(cls):
        return cls.ONLINE_ENABLED

config = Config()
config.ensure_dirs()

OFFLINE_ONLY = config.OFFLINE_ONLY
ONLINE_ENABLED = config.ONLINE_ENABLED
FULL_ACCESS = config.FULL_ACCESS
