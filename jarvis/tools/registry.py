"""
JARVIS Tools - Registry - FULL ACCESS + Human Knowledge Domains
Each tool: name, description, dangerous, required_permission, validate, execute
"""
from typing import Dict, List, Optional
from ..utils import logger

class Tool:
    name: str = "base"
    description: str = "Base tool"
    dangerous: bool = False
    required_permission: int = 1
    
    def validate(self, arguments: Dict):
        pass
    
    def execute(self, arguments: Dict):
        raise NotImplementedError

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool_instance: Tool):
        self._tools[tool_instance.name] = tool_instance
        logger.info(f"Tool registered: {tool_instance.name} (perm {tool_instance.required_permission}, dangerous={tool_instance.dangerous})")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        if name in self._tools:
            return self._tools[name]
        alias_map = {
            "open_application": "open_application", "close_application": "open_application", "list_applications": "open_application",
            "windows_control": "windows_control", "shutdown_system": "shutdown_system", "restart_system": "restart_system", "sleep_system": "sleep_system", "lock_screen": "lock_screen",
            "create_file": "create_file", "create_folder": "create_folder", "search_files": "search_files", "read_file": "read_file", "list_folders": "list_folders", "file_operation": "file_operation", "delete_file": "file_operation",
            "browser_search": "browser_search", "open_website": "open_website", "play_youtube": "play_youtube",
            "control_media": "control_media", "play_media": "play_media", "control_volume": "control_volume",
            "system_status": "system_status", "get_time": "get_time", "get_date": "get_date", "set_reminder": "set_reminder", "set_timer": "set_timer", "knowledge_query": "knowledge_query",
            "keyboard_mouse": "keyboard_mouse", "type_text": "type_text", "move_mouse": "move_mouse", "take_screenshot": "take_screenshot", "developer": "developer", "create_project": "create_project",
            "investment_advice": "investment_advice", "investment": "investment_advice",
            "business_advice": "business_advice", "business": "business_advice",
            "software_knowledge": "software_knowledge", "technology_knowledge": "technology_knowledge",
            "medical_info": "medical_info", "doctor": "medical_info",
            "legal_info": "legal_info", "lawyer": "legal_info",
            "police_info": "police_info", "police": "police_info",
            "court_info": "court_info", "court": "court_info",
            "ai_technology": "ai_technology", "ai": "ai_technology",
            "psychology_advice": "psychology_advice", "psychology": "psychology_advice",
            "autonomous_agent": "autonomous_agent", "autonomous": "autonomous_agent",
            "self_learning": "self_learning", "show_mistakes": "show_mistakes", "show_lessons": "show_lessons", "mistakes": "self_learning", "lessons": "self_learning",
        }
        real_name = alias_map.get(name)
        if real_name and real_name in self._tools:
            return self._tools[real_name]
        return None
    
    def list_tools(self) -> List[str]:
        return list(self._tools.keys())
    
    def list_tools_info(self) -> List[Dict]:
        return [{"name": t.name, "description": t.description, "dangerous": t.dangerous, "permission": t.required_permission} for t in self._tools.values()]

_registry = None

def get_tool_registry():
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_all_tools(_registry)
    return _registry

def _register_all_tools(registry: ToolRegistry):
    try:
        from .applications import ApplicationsTool
        from .windows import WindowsControlTool, ShutdownTool, RestartTool, LockScreenTool, SleepTool
        from .files import FileManagerTool, CreateFolderTool, SearchFilesTool, ReadFileTool, ListFoldersTool, FileOperationTool
        from .browser import BrowserTool, OpenWebsiteTool, PlayYoutubeTool
        from .media import MediaTool, PlayMediaTool, ControlVolumeTool
        from .system import SystemTool, GetTimeTool, GetDateTool, SetReminderTool, SetTimerTool, KnowledgeQueryTool
        from .keyboard_mouse import KeyboardMouseTool, TypeTextTool, MoveMouseTool
        from .screenshots import ScreenshotTool
        from .developer import DeveloperTool, CreateProjectTool
        from .knowledge_domains import InvestmentTool, BusinessTool, SoftwareTool, TechnologyTool, MedicalTool, LegalTool, PoliceTool, CourtTool, AITechnologyTool, PsychologyTool, AutonomousAgentTool
        from .self_learning import SelfLearningTool, ShowMistakesTool, ShowLessonsTool
        
        tools_to_register = [
            ApplicationsTool(), WindowsControlTool(), ShutdownTool(), RestartTool(), LockScreenTool(), SleepTool(),
            FileManagerTool(), CreateFolderTool(), SearchFilesTool(), ReadFileTool(), ListFoldersTool(), FileOperationTool(),
            BrowserTool(), OpenWebsiteTool(), PlayYoutubeTool(),
            MediaTool(), PlayMediaTool(), ControlVolumeTool(),
            SystemTool(), GetTimeTool(), GetDateTool(), SetReminderTool(), SetTimerTool(), KnowledgeQueryTool(),
            KeyboardMouseTool(), TypeTextTool(), MoveMouseTool(), ScreenshotTool(), DeveloperTool(), CreateProjectTool(),
            InvestmentTool(), BusinessTool(), SoftwareTool(), TechnologyTool(), MedicalTool(), LegalTool(), PoliceTool(), CourtTool(), AITechnologyTool(), PsychologyTool(), AutonomousAgentTool(),
            SelfLearningTool(), ShowMistakesTool(), ShowLessonsTool(),
        ]
        for tool in tools_to_register:
            registry.register(tool)
        logger.info(f"Registered {len(tools_to_register)} tools - FULL ACCESS + HUMAN BRAIN")
    except Exception as e:
        logger.error(f"Tool registration error: {e}", exc_info=True)
