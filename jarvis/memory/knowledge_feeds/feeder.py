"""
JARVIS Knowledge Feeder - Feeds all domain knowledge locally offline
Investment, Business, Software, Tech, Medical, Legal, Police, Court, AI
"""
import json
from pathlib import Path
from typing import Dict, List
from ...config import config
from ...utils import logger

class KnowledgeFeeder:
    def __init__(self):
        self.knowledge_dir = config.BASE_DIR / "data" / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.domains = ["investment", "business", "software", "technology", "medical", "legal", "police", "court", "ai_technologies", "psychology", "human_emotions", "fables", "mythos", "claude_intelligence"]
        self._cache = {}
        self._load_all()

    def _load_all(self):
        for domain in self.domains:
            file_path = self.knowledge_dir / f"{domain}.json"
            if file_path.exists():
                try:
                    self._cache[domain] = json.loads(file_path.read_text(encoding='utf-8'))
                except Exception as e:
                    logger.error(f"Failed to load {domain}: {e}")
            else:
                self._cache[domain] = self._get_default_knowledge(domain)
                try:
                    file_path.write_text(json.dumps(self._cache[domain], indent=2, ensure_ascii=False), encoding='utf-8')
                except Exception as e:
                    logger.error(f"Save default {domain} failed: {e}")

    def _get_default_knowledge(self, domain: str) -> Dict:
        defaults = {
            "investment": {"title": "Investment Knowledge - Offline", "disclaimer": "Educational only, not financial advice. Do own research.", "topics": {"stocks": "Stocks = company ownership. Types: large-cap (safe), mid-cap, small-cap (high risk high return). Fundamental analysis: PE ratio <20 good, Debt/Equity <1, ROE >15%. Technical: RSI, moving averages. Indian: NSE, BSE, Nifty50, Sensex. Strategy: SIP, Diversify 15-20 stocks across sectors, long term 5+ years.", "mutual_funds": "Mutual funds pool money. Types: Equity (high risk), Debt (low), Hybrid. SIP = monthly investing, rupee cost averaging. Check: expense ratio <1%, past 5yr return, fund manager. ELSS for 80C tax saving.", "crypto": "Crypto highly volatile, high risk. Bitcoin, Ethereum main. Only invest 1-5% portfolio if high risk appetite. Use hardware wallet. Avoid meme coins without research.", "gold": "Gold = hedge against inflation. Sovereign Gold Bonds best (2.5% interest + gold value). Physical gold has making charges 10-20%. Digital gold via platforms.", "real_estate": "Real estate = long term, illiquid. Check location, builder reputation, legal docs, rental yield >2-3%. Don't put all money here.", "risk_management": "Never invest emergency fund (6 months expenses). Diversify: 50% equity, 20% debt, 15% gold, 10% real estate, 5% crypto (example). Stop loss: -15% to -20%. Take profit: +30% partial."}},
            "business": {"title": "Business Knowledge", "topics": {"startup": "Lean startup: Build MVP → Measure → Learn. Business Model Canvas: Value prop, Customer, Revenue, Cost. Funding: Bootstrapped, Angel, VC. Always: Problem > Solution > Market > Team.", "marketing": "Digital marketing: SEO, Content, Social, Paid ads, Email. Traditional: Word of mouth best. 4Ps: Product, Price, Place, Promotion. Focus on retention > acquisition.", "sales": "Sales = Trust + Need + Urgency. SPIN selling: Situation, Problem, Implication, Need-payoff. Always listen more than talk.", "leadership": "Leadership = Serve team, clear vision, empower. Manage tasks, lead people. Empathy + accountability = high performance."}},
            "software": {"title": "Software & Programming", "topics": {"python": "Python easy, powerful. Use for automation, AI, web (Django/Flask/FastAPI), data. Best practices: PEP8, virtual env, type hints, tests.", "system_design": "System design: Requirements → Capacity → High level → Deep dive → Bottlenecks. Key: Scalability, Reliability, Availability. Use: Load balancer, Cache (Redis), DB sharding, CDN.", "security": "Cybersecurity: Never hardcode secrets, use HTTPS, hash passwords (bcrypt), SQL injection prevention, XSS, CSRF. Update dependencies.", "windows": "Windows control via Python: pywin32, psutil, pyautogui, PowerShell. For full laptop: file ops, registry, services, task scheduler."}},
            "technology": {"title": "Technology - Full Stack", "topics": {"ai": "AI = Machine makes human-like decisions. ML = learns from data. Deep Learning = neural networks. LLMs = text prediction. Use: Python + PyTorch/TensorFlow + HuggingFace.", "cloud": "Cloud = AWS/Azure/GCP. Services: Compute (EC2), Storage (S3), DB (RDS), AI. Learn one cloud deeply.", "networking": "Networking: OSI layers, TCP/IP, DNS, HTTP/HTTPS, VPN. Tools: Wireshark, ping, traceroute.", "latest": "2024-2026 trends: Generative AI, LLMs local (llama.cpp), Edge AI, Quantum computing early, Rust."}},
            "medical": {"title": "Medical General Knowledge - Not a Doctor Disclaimer", "disclaimer": "I am NOT a doctor. For serious issues, consult healthcare professional immediately. This is educational only.", "topics": {"general_health": "Health = Nutrition + Exercise + Sleep + Mental health. Water 2-3L/day, 7-8hr sleep, 150min exercise/week. Balanced diet: veggies, protein, whole grains, less sugar/oil.", "first_aid": "First aid: CPR (30 chest compressions + 2 breaths), bleeding → pressure, burn → cool water 20min, not ice, fracture → immobilize, don't move spine injury.", "mental_health": "Mental health = physical health. Stress management: Deep breathing 4-7-8, meditation, exercise, talk to trusted person. If severe anxiety/depression >2 weeks, seek professional help - it's strength, not weakness.", "common_symptoms": "Fever = infection likely. Headache + fever + stiff neck = urgent. Chest pain + sweating = emergency. Always: symptoms alone not diagnosis, need doctor examination + tests."}},
            "legal": {"title": "Legal Knowledge - Indian Law Basics - Not a Lawyer", "disclaimer": "Not a lawyer. For actual legal matters, consult advocate. This is educational.", "topics": {"indian_law": "Indian legal system: Constitution supreme. IPC = crimes, CrPC = procedure, CPC = civil. Rights: Fundamental rights (Article 12-35). Police cannot arrest without reason, you have right to know reason.", "cyber_law": "Cyber law India: IT Act 2000. Hacking Sec 66, Identity theft 66C, Privacy violation 66E, Publishing obscene 67. If cyber fraud: report at cybercrime.gov.in within 24hrs, call 1930.", "contracts": "Contract = Agreement + Enforceable by law. Valid contract needs: Offer, Acceptance, Consideration, Capacity, Consent, Legal object. Always written > oral, read fine print.", "property": "Property: Check title deed 30 years, encumbrance certificate, sale deed registered, mutation. Don't pay full without registration.", "consumer_rights": "Consumer rights: Right to safety, information, choice, heard, redressal, education. If cheated: Consumer forum, online at consumerhelpline.gov.in"}},
            "police": {"title": "Police Procedures - India", "topics": {"fir": "FIR = First Information Report, for cognizable offense (serious). You can file at any police station (Zero FIR), police must register (no refusal). Get copy free. If police refuses: Send to SP/DCP via post, or magistrate.", "rights": "If stopped by police: Ask reason, ask ID, you can record, right to lawyer, don't sign blank paper, right to remain silent for self-incriminating.", "cyber_police": "Cyber police: For online fraud, hacking, harassment. Keep evidence: screenshots with time, transaction IDs, don't delete chats. Report quickly."}},
            "court": {"title": "Court System India", "topics": {"hierarchy": "Hierarchy: Supreme Court (Delhi) → High Court (state) → District Court → Magistrate. Lok Adalat for settlement.", "process": "Court process: File case → Notice → Reply → Evidence → Arguments → Judgment → Appeal. Civil cases take 2-5 years average, criminal longer. Mediation faster.", "bail": "Bail: Bailable offense = easy bail at police station. Non-bailable = need court. Anticipatory bail before arrest if fear."}},
            "ai_technologies": {"title": "AI Technologies - Build Full AI Systems", "topics": {"local_llm": "Local LLM: llama.cpp + GGUF model (Qwen2, Llama3, Mistral). Run offline, no API. Use: Python llama-cpp-python, 8GB RAM for 2B model, 16GB for 7B. Prompt = system + context + user. Fine-tune with LoRA for custom knowledge.", "voice": "Voice AI: STT = faster-whisper (local), TTS = Piper (local, natural voice), Wake = openWakeWord (local). Pipeline: Mic → Wake → Record → STT → LLM → TTS. All offline, <1 sec latency with tiny models.", "autonomous_agent": "Autonomous agent: Goal → Plan → Execute → Reflect loop. Tools: file, browser, code, system. Use: ReAct prompt (Reason + Act), add memory, add self-reflection. Example: Goal 'Build portfolio website' → Plan steps → Execute each tool → Verify.", "computer_vision": "Vision: OpenCV for camera, YOLO for object detection (local), Tesseract OCR for text reading, CLIP for image understanding. All offline with ONNX models.", "build_jarvis": "To build JARVIS like Iron Man: 1) Audio stack offline 2) LLM local 3) Tools registry safe 4) Memory SQLite 5) Vision OpenCV 6) UI PySide6 7) Pack as tray app + auto-start. See ARCHITECTURE.md."}},
            "psychology": {"title": "Psychology & Human Understanding", "topics": {"empathy": "Empathy = understand other's feelings without judgment. Active listening: Listen → Reflect → Validate → Support. Example: 'I hear you feel stressed, that makes sense given...'"}},
            "human_emotions": {"title": "Human Emotions", "topics": {"all": "Humans feel: Joy, Trust, Fear, Surprise, Sadness, Disgust, Anger, Anticipation. Also: love, guilt, shame, pride. Emotions are signals, not weakness. Manage: Name it, Accept it, Breathe, Act wisely."}},
            "fables": {"title": "Fable 5 Intelligence", "topics": {"tortoise_hare": "Tortoise and Hare: Slow and steady wins race - persistence over speed, good for SIP, learning", "fox_grapes": "Fox and Grapes: Sour grapes - devalue what can't have, useful for FOMO", "lion_mouse": "Lion and Mouse: Small kindness returns big - networking", "goose_golden": "Goose Golden Eggs: Greed kills source - don't overtrade", "ant_grasshopper": "Ant and Grasshopper: Prepare for future - emergency fund"}},
            "mythos": {"title": "Mythos 5 Intelligence", "topics": {"sisyphus": "Sisyphus rolling boulder forever - futile effort without strategy, need smart work", "gita": "Gita: Duty without attachment - focus on action not anxiety of result, best for stress", "ram_dharma": "Ramayana: Dharma over short-term gain, ethics builds lasting brand", "hercules": "Hercules 12 labors: Perseverance through difficult tasks"}},
            "claude_intelligence": {"title": "Claude Level Intelligence", "topics": {"chain_of_thought": "Chain-of-thought: Break complex problem into steps: Understand -> Context -> Knowledge -> Perspectives -> Risks -> Actionable Answer -> Proactive", "self_reflection": "Self-reflection: After answer critique yourself - is it too short? Missing disclaimer? Overconfident? Hallucinated?", "self_learning": "Self-learning: Never repeat same mistake, extract pattern -> correct action, store lesson"}}}
        return defaults.get(domain, {"title": domain, "topics": {}})

    def get_domain(self, domain: str):
        return self._cache.get(domain, {})

    def search(self, query: str):
        results = []
        q = query.lower()
        q_words = set(q.split())
        for domain, data in self._cache.items():
            topics = data.get("topics", {})
            for topic_key, topic_content in topics.items():
                score = 0
                if domain.lower() in q: score += 10
                if topic_key.lower() in q: score += 8
                if q in topic_key.lower(): score += 5
                content_low = topic_content.lower()
                for word in q_words:
                    if len(word) > 3 and word in content_low: score += 1
                    if len(word) > 3 and word in topic_key.lower(): score += 2
                if any(kw in q for kw in [domain.lower()]): score += 3
                if score > 0:
                    results.append({"domain": domain, "topic": topic_key, "content": topic_content, "title": data.get("title", domain), "score": score})
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        for r in results: r.pop("score", None)
        return results[:5]

    def get_all_summary(self):
        return "\n".join([f"{d}: {list(data.get('topics', {}).keys())}" for d, data in self._cache.items()])

_feeder = None
def get_knowledge_feeder():
    global _feeder
    if _feeder is None:
        _feeder = KnowledgeFeeder()
    return _feeder
