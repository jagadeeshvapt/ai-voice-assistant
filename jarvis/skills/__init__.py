"""Load all skills"""
from .base import SKILL_REGISTRY, get_best_skill, list_skills

# Import all skills to register them
from . import time_date
from . import system_control
from . import web_search
from . import weather
from . import media
from . import knowledge
from . import automation
from . import communication

__all__ = ["SKILL_REGISTRY", "get_best_skill", "list_skills"]
