"""Preferences wrapper"""
from .database import get_memory_db

class Preferences:
    def __init__(self):
        self.db = get_memory_db()

    def get(self, key, default=None):
        return self.db.get_preference(key, default)

    def set(self, key, value):
        return self.db.set_preference(key, value)

    def get_user_name(self):
        return self.db.get_user_name()

    def set_user_name(self, name):
        return self.db.set_user_name(name)

def get_preferences():
    return Preferences()
