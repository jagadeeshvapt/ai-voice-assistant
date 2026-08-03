"""
JARVIS Core - Errors
"""
class JarvisError(Exception):
    pass

class SecurityViolation(JarvisError):
    pass

class PermissionDenied(JarvisError):
    pass

class ToolNotFound(JarvisError):
    pass

class IntentParseError(JarvisError):
    pass

class ConfirmationRequired(JarvisError):
    def __init__(self, message, intent_data=None):
        super().__init__(message)
        self.intent_data = intent_data

class PinRequired(JarvisError):
    def __init__(self, message, intent_data=None):
        super().__init__(message)
        self.intent_data = intent_data

class ModelNotFound(JarvisError):
    pass
