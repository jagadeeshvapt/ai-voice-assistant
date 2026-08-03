"""
JARVIS UI - Dashboard
Tries PySide6 first, falls back to Tkinter (old gui.py)
Strict offline
"""
from ..config import config
from ..utils import logger

def launch_dashboard(orchestrator=None):
    ui_type = config.get_yaml_config().get("ui", {}).get("dashboard", "pyside6")
    
    if ui_type == "pyside6":
        try:
            return launch_pyside_dashboard(orchestrator)
        except ImportError as e:
            logger.warning(f"PySide6 not available: {e}, fallback to tkinter")
            return launch_tk_dashboard()
        except Exception as e:
            logger.error(f"PySide6 dashboard error: {e}, fallback")
            return launch_tk_dashboard()
    else:
        return launch_tk_dashboard()

def launch_pyside_dashboard(orchestrator=None):
    try:
        from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                       QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, 
                                       QTabWidget, QListWidget)
        from PySide6.QtCore import Qt, QTimer, Signal, QObject
        from PySide6.QtGui import QFont
    except ImportError:
        raise
    
    import sys
    
    class Communicate(QObject):
        response_received = Signal(str, str)
    
    class JarvisMainWindow(QMainWindow):
        def __init__(self, orch):
            super().__init__()
            self.orch = orch
            self.comm = Communicate()
            self.comm.response_received.connect(self.add_message)
            self.init_ui()
        
        def init_ui(self):
            self.setWindowTitle("JARVIS - Local OS Assistant - Strict Offline")
            self.setGeometry(100, 100, 1100, 700)
            self.setStyleSheet("""
                QMainWindow { background-color: #0a0f1c; }
                QLabel { color: #00d4ff; }
                QTextEdit { background-color: #0e1a2e; color: #cceeff; border: 1px solid #1a3a5a; }
                QLineEdit { background-color: #1a2a4a; color: white; padding: 8px; border: 1px solid #00aaff; }
                QPushButton { background-color: #1a3a5a; color: #00ffff; padding: 8px; border: none; }
                QPushButton:hover { background-color: #2a5a8a; }
            """)
            
            central = QWidget()
            self.setCentralWidget(central)
            layout = QHBoxLayout(central)
            
            # Left - status
            left = QWidget()
            left.setMaximumWidth(250)
            left_layout = QVBoxLayout(left)
            left_layout.addWidget(QLabel("JARVIS STATUS"))
            self.status_label = QLabel("● OFFLINE\nText Mode\nStrict Offline")
            left_layout.addWidget(self.status_label)
            left_layout.addStretch()
            layout.addWidget(left)
            
            # Middle - chat
            mid = QWidget()
            mid_layout = QVBoxLayout(mid)
            mid_layout.addWidget(QLabel("CONVERSATION - Tanglish Supported"))
            self.chat = QTextEdit()
            self.chat.setReadOnly(True)
            mid_layout.addWidget(self.chat)
            
            input_layout = QHBoxLayout()
            self.input = QLineEdit()
            self.input.setPlaceholderText("Type command: Chrome open pannu, volume kammi pannu, enna time?")
            self.input.returnPressed.connect(self.send)
            self.send_btn = QPushButton("SEND")
            self.send_btn.clicked.connect(self.send)
            input_layout.addWidget(self.input)
            input_layout.addWidget(self.send_btn)
            mid_layout.addLayout(input_layout)
            
            layout.addWidget(mid)
            
            # Right - tools
            right = QWidget()
            right.setMaximumWidth(220)
            right_layout = QVBoxLayout(right)
            right_layout.addWidget(QLabel("QUICK ACTIONS"))
            quick = [
                ("Time", "what time is it"),
                ("Chrome Open", "chrome open pannu"),
                ("Volume Down", "volume kammi pannu"),
                ("Screenshot", "take screenshot"),
                ("Lock", "lock screen"),
                ("System Status", "system status"),
            ]
            for label, cmd in quick:
                btn = QPushButton(label)
                btn.clicked.connect(lambda checked, c=cmd: self.send_command(c))
                right_layout.addWidget(btn)
            right_layout.addStretch()
            layout.addWidget(right)
        
        def send(self):
            text = self.input.text().strip()
            if not text:
                return
            self.input.clear()
            self.send_command(text)
        
        def send_command(self, text):
            self.add_message("YOU", text)
            # Process in thread
            import threading
            def process():
                try:
                    if self.orch:
                        result = self.orch.process_text(text)
                        resp = result.get("response", "")
                    else:
                        from ..core.orchestrator import get_orchestrator
                        orch = get_orchestrator()
                        result = orch.process_text(text)
                        resp = result.get("response", "")
                    self.comm.response_received.emit("JARVIS", resp)
                    if self.orch:
                        self.orch.speak(resp)
                except Exception as e:
                    self.comm.response_received.emit("ERROR", str(e))
            
            threading.Thread(target=process, daemon=True).start()
        
        def add_message(self, sender, msg):
            self.chat.append(f"<b>{sender}:</b> {msg}\n")
    
    app = QApplication(sys.argv)
    orch = orchestrator
    if not orch:
        try:
            from ..core.orchestrator import get_orchestrator
            orch = get_orchestrator()
            orch.start()
        except Exception as e:
            logger.error(f"Orchestrator start in dashboard failed: {e}")
    
    window = JarvisMainWindow(orch)
    window.show()
    sys.exit(app.exec())

def launch_tk_dashboard():
    # Fallback to old tkinter gui
    try:
        import gui
        gui.main()
    except Exception as e:
        logger.error(f"Tk dashboard failed: {e}")
        print("Dashboard failed, use text mode: python app.py --text")
