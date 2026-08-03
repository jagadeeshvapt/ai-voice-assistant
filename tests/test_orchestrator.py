"""Test orchestrator end-to-end"""
from jarvis.core.orchestrator import get_orchestrator

def test_orchestrator():
    orch = get_orchestrator()
    
    tests = [
        "what time is it",
        "enna time",
        "system status sollu",
        "volume kammi pannu",
        "Chrome open pannu",
        "take screenshot",
    ]
    
    for t in tests:
        result = orch.process_text(t)
        print(f"\nQ: {t}")
        print(f"  Intent: {result['intent']['intent']} | Confidence: {result['intent']['confidence']}")
        print(f"  A: {result['response']}")
        assert result['response'], f"No response for {t}"
    
    print("\nAll orchestrator tests passed!")

if __name__ == "__main__":
    test_orchestrator()
