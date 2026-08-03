"""Test intent parsing and permission levels"""
from jarvis.language.intent_parser import get_intent_parser
from jarvis.security.permissions import get_permission_manager

def test_intents():
    parser = get_intent_parser()
    perm = get_permission_manager()
    
    tests = [
        ("what time is it", "get_time", 0),
        ("Chrome open pannu", "open_application", 1),
        ("volume kammi pannu", "control_volume", 1),
        ("take screenshot", "take_screenshot", 1),
        ("shutdown pannu", "shutdown_system", 3),
        ("delete file test.txt", "file_operation", 2),
    ]
    
    for text, expected_intent, expected_level in tests:
        intent = parser.parse(text.lower(), text)
        print(f"Text: {text} -> Intent: {intent}")
        if intent:
            assert intent['intent'] == expected_intent or expected_intent in intent['intent'], f"Expected {expected_intent}, got {intent['intent']}"
            assert perm.get_level(intent) == expected_level, f"Level mismatch for {text}"
            print(f"  ✓ Level {expected_level} OK")
        else:
            print(f"  ✗ No intent parsed for {text}")

if __name__ == "__main__":
    test_intents()
    print("Intent tests completed")
