"""
JARVIS Core - Autonomous Agent
Human-like thinking, multi-step planning, self-reflection
"""
import time
from typing import List, Dict, Callable
from ..utils import logger
from .state import get_state_manager, AssistantState

class AutonomousAgent:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.state = get_state_manager()
        self.max_steps = 10

    def execute_goal(self, goal: str, callback: Callable = None) -> Dict:
        """
        Execute a goal autonomously like human would
        Plan → Execute → Reflect → Adapt
        """
        from ..tools.knowledge_domains import AutonomousAgentTool
        planner = AutonomousAgentTool()
        plan_text = planner.execute({"goal": goal})
        
        # Parse steps
        steps = []
        for line in plan_text.split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line[:3]:
                steps.append(line.split(".",1)[1].strip())
        
        if not steps:
            steps = [f"Step for: {goal}"]
        
        results = []
        logger.info(f"Autonomous execution: {goal} -> {len(steps)} steps")
        
        for i, step in enumerate(steps, 1):
            if i > self.max_steps:
                break
            
            self.state.set_state(AssistantState.THINKING, {"step": i, "goal": goal, "current": step})
            
            if callback:
                callback({"type": "step_start", "step": i, "total": len(steps), "action": step})
            
            # Execute step via orchestrator
            try:
                if self.orchestrator:
                    result = self.orchestrator.process_text(step)
                    results.append({"step": step, "result": result.get("response", ""), "success": True})
                    if callback:
                        callback({"type": "step_done", "step": i, "response": result.get("response","")})
                else:
                    results.append({"step": step, "result": f"Would execute: {step}", "success": True})
            except Exception as e:
                results.append({"step": step, "result": f"Failed: {e}", "success": False})
                logger.error(f"Autonomous step {i} failed: {e}")
            
            time.sleep(0.5)  # Small delay for human-like pacing
        
        self.state.set_state(AssistantState.IDLE)
        
        # Self-reflection
        reflection = self._reflect(goal, results)
        
        return {
            "goal": goal,
            "steps": steps,
            "results": results,
            "reflection": reflection,
            "success": all(r["success"] for r in results)
        }

    def _reflect(self, goal: str, results: List[Dict]) -> str:
        """Human-like self-reflection after execution"""
        success_count = sum(1 for r in results if r["success"])
        total = len(results)
        
        if success_count == total:
            return f"Mudichiten Sir! Goal '{goal}' full-a complete panniten. {total} steps ellam success. Vera edhavadhu venuma?"
        elif success_count > total/2:
            return f"Mostly mudichiten Sir ({success_count}/{total} steps). Konjam steps la issue vandhuchu, but overall progress good. Continue pannalama?"
        else:
            return f"Goal '{goal}' la konjam difficulties vandhuchu Sir. {success_count}/{total} dhan success. Vera approach try pannalama?"

# Singleton
_agent = None

def get_autonomous_agent(orchestrator=None):
    global _agent
    if _agent is None:
        _agent = AutonomousAgent(orchestrator)
    return _agent
