"""
JARVIS Core - Orchestrator - Human-like Full Access
Flow: Mic -> Wake -> Record -> STT -> Tanglish Normalizer + Empathy -> Intent Router -> LLM Planner (human brain) -> Permissions -> Tool Executor (full C:/D:/ + knowledge domains) -> Memory -> TTS
Strict offline, modular, safe
"""
import time
import threading
import datetime
from typing import Optional, Dict, Any

from ..config import config
from ..utils import logger
from .state import get_state_manager, AssistantState
from .event_bus import get_event_bus, Event
from .errors import ConfirmationRequired, PinRequired, SecurityViolation, ToolNotFound

class Orchestrator:
    def __init__(self, text_mode: bool = None):
        if text_mode is not None:
            config.TEXT_MODE = text_mode
        
        self.config = config
        self.state = get_state_manager()
        self.events = get_event_bus()
        
        self._audio_mic = None
        self._wake_detector = None
        self._recorder = None
        self._stt = None
        self._tts = None
        self._normalizer = None
        self._intent_parser = None
        self._llm = None
        self._response_formatter = None
        self._permissions = None
        self._confirmations = None
        self._pin_manager = None
        self._audit = None
        self._memory_db = None
        self._tool_registry = None
        
        self._running = False
        self._stop_event = threading.Event()
        self._pending_confirmation: Optional[Dict] = None
        
        self._init_components()

    def _init_components(self):
        logger.info("Initializing JARVIS Core components (FULL ACCESS + Human Brain + Self-Learning + Claude)")
        try:
            from ..memory import get_memory_db
            self._memory_db = get_memory_db()
            from ..memory.self_learning import get_self_learning_engine
            self._self_learning = get_self_learning_engine()
            from ..security.audit_log import get_audit_log
            self._audit = get_audit_log()
            from ..security.permissions import get_permission_manager
            self._permissions = get_permission_manager()
            from ..security.confirmations import get_confirmation_manager
            self._confirmations = get_confirmation_manager()
            from ..security.pin import get_pin_manager
            self._pin_manager = get_pin_manager()
            from ..language.tanglish_normalizer import get_normalizer
            self._normalizer = get_normalizer()
            from ..language.intent_parser import get_intent_parser
            self._intent_parser = get_intent_parser()
            from ..language.local_llm import get_llm
            self._llm = get_llm()
            from ..language.response_formatter import get_response_formatter
            self._response_formatter = get_response_formatter()
            from ..language.claude_level_intelligence import get_claude_intelligence
            self._claude = get_claude_intelligence()
            from ..tools.registry import get_tool_registry
            self._tool_registry = get_tool_registry()
            from ..audio.microphone import get_microphone
            from ..audio.speech_to_text import get_stt
            from ..audio.text_to_speech import get_tts
            from ..audio.wake_word import get_wake_detector
            self._audio_mic = get_microphone()
            self._stt = get_stt()
            self._tts = get_tts()
            self._wake_detector = get_wake_detector()
            logger.info("All core components initialized - FULL ACCESS + HUMAN BRAIN + SELF-LEARNING + CLAUDE")
        except Exception as e:
            logger.error(f"Component init failed: {e}", exc_info=True)

    def start(self):
        self._running = True
        self._stop_event.clear()
        self.state.set_state(AssistantState.IDLE)
        self.events.publish_sync("jarvis.started", {"time": datetime.datetime.now().isoformat()})
        from ..memory.reminders import get_reminder_manager
        self._reminder_manager = get_reminder_manager()
        self._reminder_manager.start(callback=self._on_reminder_due)
        logger.info("JARVIS Orchestrator started - FULL ACCESS OFFLINE")

    def stop(self):
        self._running = False
        self._stop_event.set()
        self.state.set_state(AssistantState.OFFLINE)
        try: self._audio_mic.stop()
        except: pass
        try: self._wake_detector.stop()
        except: pass
        try: self._reminder_manager.stop()
        except: pass
        self.events.publish_sync("jarvis.stopped")

    def greet(self) -> str:
        from ..utils import get_greeting
        greeting = get_greeting()
        try:
            user_name = self._memory_db.get_user_name() if hasattr(self._memory_db, 'get_user_name') else "Sir"
        except:
            user_name = "Sir"
        now = datetime.datetime.now()
        msg = f"{greeting}, {user_name}. Full laptop access enabled - C:/, D:/, all drives. Human-like brain online. All knowledge domains fed: investment, business, medical, legal, AI. Enna help venum?"
        self.events.publish_sync("jarvis.greeting", {"message": msg})
        return msg

    def process_text(self, raw_text: str, source: str = "user") -> Dict[str, Any]:
        start_time = time.time()
        self.state.set_state(AssistantState.THINKING, {"input": raw_text})
        result = {"input_raw": raw_text, "input_normalized": "", "language": "en", "intent": None, "tool_result": None, "response": "", "requires_confirmation": False, "confirmation_id": None, "execution_time": 0}
        try:
            self.state.set_state(AssistantState.TRANSCRIBING)
            from ..language.empathy_engine import get_empathy_engine
            empathy_engine = get_empathy_engine()
            empathy_analysis = empathy_engine.analyze(raw_text)
            normalized, meta = self._normalizer.normalize(raw_text)
            result["input_normalized"] = normalized
            result["language"] = meta.get("language", "en")
            result["tanglish_meta"] = meta
            result["empathy_analysis"] = empathy_analysis
            result["detected_emotion"] = empathy_analysis.get("emotion", "neutral")
            logger.info(f"NORMALIZED: '{raw_text}' -> '{normalized}' [{meta}] Emotion: {empathy_analysis}")

            # SELF-LEARNING: Check if this is a correction to previous mistake
            # Skip correction check for explicit self-learning queries
            is_self_learning_query = any(kw in raw_text.lower() for kw in ["show mistakes", "show lessons", "list mistakes", "view lessons", "self learning"])
            
            if not is_self_learning_query and self._self_learning.is_correction(raw_text) and hasattr(self, '_last_result') and self._last_result:
                last = self._last_result
                # Don't learn if last was itself a self-learning response
                if last.get("intent", {}).get("intent") in ("self_learning", "show_mistakes", "show_lessons"):
                    pass  # Skip, don't treat as correction to self-learning stats
                else:
                    last_query = last.get("input_raw", "")
                    last_intent = last.get("intent", {}).get("intent", "") if last.get("intent") else ""
                    last_response = last.get("response", "")
                    # Learn from correction
                    learn_result = self._self_learning.learn_mistake(last_query, last_response, last_intent, raw_text)
                    logger.info(f"Self-learning: Learned from correction: {learn_result}")
                    result["self_learning"] = learn_result
                    result["response"] = f"Got it Sir! Lesson learned: {learn_result.get('lesson','')[:200]}. I won't repeat this mistake. Thanks for correcting me!"
                    result["intent"] = {"intent": "self_learning", "confidence": 1.0}
                    self._last_result = result
                    return self._finalize_result(result, start_time)

            # SELF-LEARNING: Before answering, check lessons to prevent repeating mistake
            lessons = self._self_learning.get_lessons_for_query(raw_text)
            if lessons:
                logger.info(f"Self-learning: Found {len(lessons)} relevant lessons for '{raw_text}': {lessons[0]['lesson'][:100]}")
                result["relevant_lessons"] = lessons

            if self._pending_confirmation:
                pending = self._pending_confirmation
                if pending.get("type") == "pin":
                    from ..security.pin import get_pin_manager
                    pin_manager = get_pin_manager()
                    if pin_manager.verify_pin(raw_text):
                        self._pending_confirmation = None
                        self.state.set_state(AssistantState.EXECUTING)
                        intent_data = pending["intent_data"]
                        intent_data["pin_verified"] = True
                        intent_data["confirmed"] = True
                        tool_result = self._execute_with_permissions(intent_data, confirmed=True)
                        result["tool_result"] = tool_result
                        response = self._response_formatter.format_tool_result(intent_data, tool_result, language=result["language"])
                        result["response"] = response
                        self._save_and_audit(raw_text, intent_data, tool_result, confirmed=True)
                        return self._finalize_result(result, start_time)
                    elif self._confirmations.is_confirmation(normalized):
                        if not config.REQUIRE_PIN_ADMIN:
                            self._pending_confirmation = None
                            self.state.set_state(AssistantState.EXECUTING)
                            intent_data = pending["intent_data"]
                            intent_data["confirmed"] = True
                            tool_result = self._execute_with_permissions(intent_data, confirmed=True)
                            result["tool_result"] = tool_result
                            response = self._response_formatter.format_tool_result(intent_data, tool_result, language=result["language"])
                            result["response"] = response
                            self._save_and_audit(raw_text, intent_data, tool_result, confirmed=True)
                            return self._finalize_result(result, start_time)
                        else:
                            result["response"] = "PIN thappu Sir, sariyana PIN sollunga. Default PIN 1234."
                            return self._finalize_result(result, start_time)
                    elif self._confirmations.is_denial(normalized):
                        result["response"] = self._response_formatter.format_denial(result["language"])
                        self._pending_confirmation = None
                        self.state.set_state(AssistantState.IDLE)
                        return self._finalize_result(result, start_time)
                    else:
                        result["response"] = "PIN sollunga Sir, illa 'cancel' sollunga."
                        return self._finalize_result(result, start_time)
                if self._confirmations.is_confirmation(normalized):
                    pending = self._pending_confirmation
                    self._pending_confirmation = None
                    self.state.set_state(AssistantState.EXECUTING)
                    tool_result = self._execute_with_permissions(pending["intent_data"], confirmed=True)
                    result["tool_result"] = tool_result
                    response = self._response_formatter.format_tool_result(pending["intent_data"], tool_result, language=result["language"])
                    result["response"] = response
                    self._save_and_audit(raw_text, pending["intent_data"], tool_result, confirmed=True)
                    return self._finalize_result(result, start_time)
                elif self._confirmations.is_denial(normalized):
                    result["response"] = self._response_formatter.format_denial(result["language"])
                    self._pending_confirmation = None
                    self.state.set_state(AssistantState.IDLE)
                    return self._finalize_result(result, start_time)

            self.state.set_state(AssistantState.THINKING)
            
            # CLAUDE-LEVEL: Chain-of-thought reasoning before intent parsing
            claude_thought = self._claude.chain_of_thought(raw_text, domain="general")
            result["claude_thought"] = claude_thought
            logger.debug(f"Claude CoT: {claude_thought}")

            # Check self-learning lessons first - if past mistake, use correct action directly (never repeat mistake)
            lessons = result.get("relevant_lessons", [])
            intent_data = None
            if lessons:
                # If lesson has correct_action that looks like an intent, try to use it
                for lesson in lessons:
                    correct_action = lesson.get("correct_action", "")
                    # If correct_action is short and looks like intent correction, try to parse it
                    if len(correct_action) < 100 and any(kw in correct_action.lower() for kw in ["open", "volume", "investment", "business"]):
                        # Extract intent from correct_action if possible
                        maybe_intent = self._intent_parser.parse(correct_action.lower(), correct_action)
                        if maybe_intent and maybe_intent.get("confidence",0) > 0.6:
                            intent_data = maybe_intent
                            logger.info(f"Self-learning APPLIED lesson: using corrected intent {intent_data} instead of re-parsing")
                            break

            if not intent_data:
                intent_data = self._intent_parser.parse(normalized, raw_text)
                raw_intent = self._intent_parser.parse(raw_text.lower(), raw_text)
                if raw_intent and (not intent_data or raw_intent.get("confidence", 0) > intent_data.get("confidence", 0)):
                    intent_data = raw_intent
            # REAL JARVIS FIX: Increased thresholds from 0.6/0.7 to 0.8/0.9 so LLM can override weak knowledge_query (0.6) with strong get_time (0.99)
            # Example: "time and what is the time right now" was parsed as knowledge_query 0.6, but LLM correctly gives get_time 0.99 - should override
            if not intent_data or intent_data.get("confidence", 0) < 0.8:
                llm_intent = self._llm.plan(normalized, context=self._memory_db.get_context_for_llm() if hasattr(self._memory_db, 'get_context_for_llm') else "")
                if llm_intent and (not intent_data or llm_intent.get("confidence", 0) > intent_data.get("confidence", 0)):
                    intent_data = llm_intent
                    logger.info(f"LLM overrode intent parser: {llm_intent} (was {intent_data})")
                if not intent_data or intent_data.get("confidence", 0) < 0.9:
                    llm_raw = self._llm.plan(raw_text, context=self._memory_db.get_context_for_llm() if hasattr(self._memory_db, 'get_context_for_llm') else "")
                    if llm_raw and (not intent_data or llm_raw.get("confidence", 0) > intent_data.get("confidence", 0)):
                        intent_data = llm_raw
                        logger.info(f"LLM raw overrode: {llm_raw}")
            if not intent_data:
                raise Exception("Could not understand intent")
            
            # SELF-LEARNING: Check if this intent would repeat past mistake
            should_correct, lesson = self._self_learning.should_correct_intent(raw_text, intent_data.get("intent",""))
            if should_correct:
                logger.info(f"Self-learning PREVENTED repeating mistake: {lesson}")
                # Try to get correct intent from lesson
                corrected = self._intent_parser.parse(lesson.get("correct_action",""), lesson.get("correct_action",""))
                if corrected:
                    intent_data = corrected
                    result["self_learning_prevented"] = True
                    result["prevented_lesson"] = lesson

            result["intent"] = intent_data
            logger.info(f"INTENT: {intent_data}")

            try:
                self._permissions.check_permission(intent_data)
            except ConfirmationRequired as e:
                confirmation_id = self._confirmations.create_confirmation(intent_data)
                self._pending_confirmation = {"id": confirmation_id, "intent_data": intent_data, "raw": raw_text, "type": "confirmation"}
                self.state.set_state(AssistantState.CONFIRMING, {"confirmation_id": confirmation_id})
                response = e.args[0] if e.args else self._response_formatter.format_confirmation_request(intent_data, language=result["language"])
                result["response"] = response
                result["requires_confirmation"] = True
                result["confirmation_id"] = confirmation_id
                return self._finalize_result(result, start_time)
            except PinRequired as e:
                confirmation_id = self._confirmations.create_confirmation(intent_data)
                self._pending_confirmation = {"id": confirmation_id, "intent_data": intent_data, "raw": raw_text, "type": "pin"}
                self.state.set_state(AssistantState.CONFIRMING, {"confirmation_id": confirmation_id})
                result["response"] = str(e) + " PIN required. Voice PIN sollunga or type pannunga. Or say 'yes' to proceed if PIN disabled in config."
                result["requires_confirmation"] = True
                result["needs_pin"] = True
                result["confirmation_id"] = confirmation_id
                return self._finalize_result(result, start_time)

            self.state.set_state(AssistantState.EXECUTING)
            tool_result = self._execute_with_permissions(intent_data, confirmed=False)
            result["tool_result"] = tool_result

            base_response = self._response_formatter.format_tool_result(intent_data, tool_result, language=result["language"])
            empathetic_response = empathy_engine.enhance_response(base_response, result.get("empathy_analysis", {}), domain=intent_data.get("intent"))

            # CLAUDE-LEVEL: Add fable/mythos wisdom where relevant
            try:
                fable_key, fable_data = self._claude.get_relevant_fable(raw_text)
                mythos_key, mythos_data = self._claude.get_relevant_mythos(raw_text)
                # Add wisdom if domain is investment, business, stress, etc
                if intent_data.get("intent") in ["investment_advice", "business_advice", "psychology_advice", "technology_knowledge"] and fable_data:
                    empathetic_response += f"\n\n📖 Fable wisdom like {fable_data['title']}: {fable_data['moral']} - {fable_data['lesson']}"
                # Self-reflection like Claude
                reflection = self._claude.self_reflect(empathetic_response, raw_text)
                result["claude_reflection"] = reflection
                if reflection.get("should_revise"):
                    logger.info(f"Claude self-reflection suggests revise: {reflection['critique']}")
                    # Could revise here, but for now log
            except Exception as e:
                logger.debug(f"Claude wisdom add failed: {e}")

            result["response"] = empathetic_response

            self._save_and_audit(raw_text, intent_data, tool_result, confirmed=False)
            # Store last result for self-learning correction detection
            self._last_result = result
            return self._finalize_result(result, start_time)
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            result["response"] = self._response_formatter.format_error(str(e), language=result.get("language", "en"))
            result["error"] = str(e)
            return self._finalize_result(result, start_time)
        finally:
            self.state.set_state(AssistantState.IDLE)

    def _execute_with_permissions(self, intent_data: Dict, confirmed: bool = False):
        tool_name = intent_data.get("intent")
        arguments = intent_data.get("arguments", {})
        if confirmed:
            self._permissions.mark_confirmed(intent_data)
        tool = self._tool_registry.get_tool(tool_name)
        if not tool:
            from ..skills import get_best_skill
            legacy_skill, score = get_best_skill(intent_data.get("arguments", {}).get("raw", "") or str(arguments))
            if legacy_skill and score >= 1:
                raw = arguments.get("raw", "") or intent_data.get("reply", "")
                return legacy_skill.handle(raw or tool_name)
            raise ToolNotFound(f"Tool {tool_name} not found")
        tool.validate(arguments)
        result = tool.execute(arguments)
        return result

    def _save_and_audit(self, raw_text: str, intent_data: Dict, tool_result: Any, confirmed: bool):
        try:
            self._memory_db.add_conversation(raw_text, intent_data, tool_result)
        except Exception as e:
            logger.error(f"Memory save failed: {e}")
        try:
            self._audit.log(command=raw_text, intent=intent_data.get("intent"), arguments=intent_data.get("arguments"), result=str(tool_result)[:500], confirmed=confirmed, permission_level=intent_data.get("permission_level", 0))
        except Exception as e:
            logger.error(f"Audit log failed: {e}")

    def _finalize_result(self, result: Dict, start_time: float):
        result["execution_time"] = time.time() - start_time
        result["timestamp"] = datetime.datetime.now().isoformat()
        self.events.publish_sync("jarvis.response", result)
        self.state.set_state(AssistantState.IDLE)
        return result

    def speak(self, text: str):
        if not text:
            return
        self.state.set_state(AssistantState.SPEAKING, {"text": text})
        try:
            self._tts.speak(text)
        except Exception as e:
            logger.error(f"TTS speak error: {e}")
        finally:
            self.state.set_state(AssistantState.IDLE)

    def _on_reminder_due(self, reminder: Dict):
        msg = f"Reminder Sir: {reminder.get('text', '')}"
        self.speak(msg)
        self.events.publish_sync("reminder.due", reminder)

    def listen_loop(self, callback):
        self.state.set_state(AssistantState.LISTENING_WAKEWORD)
        def on_wake(command: str):
            self.state.set_state(AssistantState.LISTENING_COMMAND)
            result = self.process_text(command)
            response = result.get("response", "")
            if response:
                self.speak(response)
                callback(result)
        if config.TEXT_MODE:
            while self._running and not self._stop_event.is_set():
                try:
                    raw = input("\n[You - Type] > ").strip()
                    if not raw:
                        continue
                    if raw.lower() in ("exit", "quit", "bye"):
                        self.stop()
                        break
                    result = self.process_text(raw)
                    print(f"\n[JARVIS] {result['response']}\n")
                    callback(result)
                except KeyboardInterrupt:
                    break
        else:
            try:
                self._wake_detector.start(on_wake)
                while self._running and not self._stop_event.is_set():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
            finally:
                self.stop()

_orchestrator = None
def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
