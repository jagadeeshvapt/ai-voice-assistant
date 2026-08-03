"""
JARVIS Tools - Knowledge Domains - Investment, Business, Medical, Legal, AI etc
All local offline knowledge, with human-like advice + disclaimers
"""
from typing import Dict
from .registry import Tool
from ..memory.knowledge_feeds.feeder import get_knowledge_feeder
from ..language.empathy_engine import get_empathy_engine
from ..utils import logger

class BaseKnowledgeTool(Tool):
    domain: str = "investment"
    description = "Knowledge domain"
    required_permission = 0
    dangerous = False

    def __init__(self):
        self.feeder = get_knowledge_feeder()
        self.empathy = get_empathy_engine()

    def validate(self, args: Dict):
        pass

    def execute(self, args: Dict):
        query = args.get("query") or args.get("text") or args.get("raw") or ""
        # Search feeder
        domain_data = self.feeder.get_domain(self.domain)
        
        # If query empty, return summary
        if not query or len(query.split()) < 2:
            topics = domain_data.get("topics", {})
            summary = f"{domain_data.get('title', self.domain)} - Topics: {', '.join(topics.keys())}. Ask: '{self.domain} explain stocks' or '{self.domain} help'"
            if domain_data.get("disclaimer"):
                summary += f"\n\nDisclaimer: {domain_data['disclaimer']}"
            return summary
        
        # Search
        results = self.feeder.search(query)
        # Filter by domain if possible
        domain_results = [r for r in results if r['domain'] == self.domain]
        if domain_results:
            best = domain_results[0]
        elif results:
            best = results[0]
        else:
            # Search within domain topics directly
            topics = domain_data.get("topics", {})
            best_match = None
            q_low = query.lower()
            for k, v in topics.items():
                if k.lower() in q_low or q_low in v.lower():
                    best_match = {"topic": k, "content": v, "domain": self.domain, "title": domain_data.get("title")}
                    break
            if best_match:
                best = best_match
            else:
                # Return general
                return f"{self.domain} - I have knowledge on: {', '.join(domain_data.get('topics', {}).keys())}. Try: '{query}' more specific. Example: '{self.domain} explain {list(domain_data.get('topics', {}).keys())[0] if domain_data.get('topics') else 'stocks'}'"
        
        # Format with empathy if needed
        content = best.get("content", "")[:1500]
        title = best.get("title", "")
        topic = best.get("topic", "")
        
        response = f"**{title} - {topic.title()}**\n{content}"
        
        if domain_data.get("disclaimer"):
            response += f"\n\n⚠️ {domain_data['disclaimer']}"
        
        # Add empathetic closing if emotional context
        analysis = self.empathy.analyze(query)
        if analysis.get("needs_empathy"):
            empathetic = self.empathy.get_empathetic_opening(analysis)
            if empathetic:
                response = f"{empathetic}\n\n{response}"
        
        # Add actionable next steps for human-like
        if self.domain == "investment":
            response += "\n\nNext: Pesunga Sir, unga risk appetite enna? Long term-a short term-a? Naan portfolio suggest pannalam."
        elif self.domain == "business":
            response += "\n\nNext: Unga business idea enna? Naan business plan create panni thara."
        elif self.domain == "medical":
            response += "\n\nRemember: Serious ah irundha doctor kitta ponga Sir, naan general info dhan. Enakku vera help venuma?"
        elif self.domain == "legal":
            response += "\n\nNote: Actual case ku lawyer kitta poi pesunga Sir. General info dhan idhu."
        
        return response

class InvestmentTool(BaseKnowledgeTool):
    name = "investment_advice"
    description = "Investment knowledge: stocks, mutual funds, crypto, gold, real estate"
    domain = "investment"

class BusinessTool(BaseKnowledgeTool):
    name = "business_advice"
    description = "Business knowledge: startup, marketing, sales, leadership"
    domain = "business"

class SoftwareTool(BaseKnowledgeTool):
    name = "software_knowledge"
    description = "Software & programming knowledge"
    domain = "software"

class TechnologyTool(BaseKnowledgeTool):
    name = "technology_knowledge"
    description = "Technology full stack knowledge"
    domain = "technology"

class MedicalTool(BaseKnowledgeTool):
    name = "medical_info"
    description = "Medical general information (not a doctor) - health, first aid, mental health"
    domain = "medical"

class LegalTool(BaseKnowledgeTool):
    name = "legal_info"
    description = "Legal info Indian law, cyber law, contracts (not a lawyer)"
    domain = "legal"

class PoliceTool(BaseKnowledgeTool):
    name = "police_info"
    description = "Police procedures, FIR, rights in India"
    domain = "police"

class CourtTool(BaseKnowledgeTool):
    name = "court_info"
    description = "Court system India, bail, process"
    domain = "court"

class AITechnologyTool(BaseKnowledgeTool):
    name = "ai_technology"
    description = "AI technologies: local LLM, voice AI, autonomous agents, how to build JARVIS"
    domain = "ai_technologies"

class PsychologyTool(BaseKnowledgeTool):
    name = "psychology_advice"
    description = "Human psychology, empathy, emotional support"
    domain = "psychology"

# Autonomous agent tool that plans multi-step

class AutonomousAgentTool(Tool):
    name = "autonomous_agent"
    description = "Autonomous agent that breaks big goals into steps and executes"
    required_permission = 1
    dangerous = False

    def validate(self, args):
        pass

    def execute(self, args):
        goal = args.get("goal") or args.get("query") or args.get("raw") or ""
        if not goal:
            return "Goal sollunga Sir. Example: 'Build a python project for portfolio website'"
        
        # Simple autonomous planner - break goal into steps
        steps = self._plan_steps(goal)
        
        response = f"**Autonomous Agent - Goal: {goal}**\n\nI will think like human and break this into steps:\n"
        for i, step in enumerate(steps, 1):
            response += f"{i}. {step}\n"
        
        response += "\nNaan ippo autonomous ah execute pannava? Say 'yes' to start, or I can explain each step."
        
        # Save plan to memory for execution
        from ..memory.database import get_memory_db
        db = get_memory_db()
        db.learn_fact(f"autonomous_plan_{goal[:20]}", "\n".join(steps))
        
        return response

    def _plan_steps(self, goal: str) -> list:
        low = goal.lower()
        if "portfolio website" in low:
            return [
                "Create project folder workspace/portfolio",
                "Create index.html with basic structure",
                "Create style.css for design",
                "Create script.js for interactivity",
                "Test locally by opening in browser",
                "Create README with instructions"
            ]
        if "python project" in low:
            return [
                "Create project folder workspace/my_project",
                "Create main.py, requirements.txt, README.md",
                "Write starter code",
                "Create .gitignore",
                "Open VS Code for editing"
            ]
        if "investment" in low:
            return [
                "Understand your risk appetite and goals",
                "Analyze current financial situation",
                "Research options: stocks, mutual funds, gold",
                "Create diversified portfolio plan",
                "Set up SIP and emergency fund"
            ]
        if "business" in low:
            return [
                "Clarify problem and solution",
                "Define target customer and market size",
                "Create Business Model Canvas",
                "Build MVP first",
                "Plan marketing and funding"
            ]
        # Generic
        return [
            f"Analyze goal: {goal}",
            "Break into small tasks",
            "Prioritize tasks (important vs urgent)",
            "Execute step by step with tools",
            "Review and improve"
        ]
