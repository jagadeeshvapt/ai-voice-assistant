"""
JARVIS Tools - Self Learning Management
View lessons, mistakes, stats - never make same mistake again
"""
from typing import Dict
from .registry import Tool
from ..memory.self_learning import get_self_learning_engine

class SelfLearningTool(Tool):
    name = "self_learning"
    description = "View self-learning stats, mistakes, lessons - shows how JARVIS learns from mistakes"
    required_permission = 0

    def validate(self, args):
        pass

    def execute(self, args):
        raw = (args.get("raw") or "").lower()
        engine = get_self_learning_engine()
        
        if "mistakes" in raw or "errors" in raw:
            mistakes = engine.list_recent_mistakes(10)
            if not mistakes:
                return "No mistakes recorded yet Sir - clean record! Self-learning active, will never repeat mistakes."
            txt = "Recent mistakes & lessons learned (I won't repeat these):\n"
            for m in mistakes:
                txt += f"- Q: {m['query'][:50]} | Wrong: {m['wrong'][:40]} -> Correct: {m['correct'][:40]} | Lesson: {m['lesson'][:80]} | Times: {m['times']}\n"
            return txt
        
        if "lessons" in raw:
            stats = engine.get_mistake_stats()
            return f"Self-learning lessons: {stats.get('lessons',0)} lessons from {stats.get('total_mistakes',0)} mistakes (seen {stats.get('total_times_seen',0)} times). Fixed: {stats.get('fixed',0)}. I never repeat same mistake Sir!"
        
        # Stats
        stats = engine.get_mistake_stats()
        return f"""**JARVIS Self-Learning Engine - Like Claude**

Stats:
- Total mistakes tracked: {stats.get('total_mistakes',0)}
- Times mistakes seen: {stats.get('total_times_seen',0)}
- Lessons learned: {stats.get('lessons',0)}
- Feedbacks: {stats.get('feedbacks',0)}
- Corrections: {stats.get('corrections',0)}
- Fixed: {stats.get('fixed',0)}

How I learn:
1. When I make mistake and you say 'wrong', 'thappu', 'correct is X', I store lesson
2. Next time same query, I check lessons first and apply correct action - never repeat
3. Chain-of-thought + self-reflection like Claude

Try: 'show mistakes' or 'show lessons' or just correct me when I'm wrong: 'No, correct is open chrome'"""

class ShowMistakesTool(SelfLearningTool):
    name = "show_mistakes"
    description = "Shows recent mistakes JARVIS learned from"

class ShowLessonsTool(SelfLearningTool):
    name = "show_lessons"
    description = "Shows lessons learned"
