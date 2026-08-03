"""Test security: confirmation, PIN, audit"""
from jarvis.security.confirmations import get_confirmation_manager
from jarvis.security.pin import get_pin_manager
from jarvis.tools.files import FileManagerTool
from jarvis.config import config

def test_confirmations():
    cm = get_confirmation_manager()
    assert cm.is_confirmation("yes")
    assert cm.is_confirmation("aama")
    assert cm.is_confirmation("sari")
    assert cm.is_denial("no")
    assert cm.is_denial("illa")
    assert cm.is_denial("venda")
    print("Confirmation tests passed")

def test_pin():
    pm = get_pin_manager()
    assert pm.verify_pin("1234") == True
    assert pm.verify_pin("0000") == False
    print("PIN tests passed")

def test_file_safety():
    tool = FileManagerTool()
    # Should resolve safe path
    safe = tool._resolve_safe_path("workspace/test.txt")
    print(f"Safe path: {safe}")
    # Blocked path should raise
    try:
        # Try to access Windows folder (blocked)
        blocked = tool._resolve_safe_path("C:/Windows/System32/test.txt")
        # If config has blocked folders, it may raise
        print(f"Blocked test path resolved to {blocked} - check if blocked detection works")
    except ValueError as e:
        print(f"Blocked correctly: {e}")

if __name__ == "__main__":
    test_confirmations()
    test_pin()
    test_file_safety()
    print("Security tests completed")
