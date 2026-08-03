#!/usr/bin/env python3
"""
JARVIS GUI - Futuristic HUD like Iron Man

Features:
- Animated arc reactor
- Voice waveform visualization
- Chat history
- System status
- Vision feed (if enabled)
- Skill shortcuts

Run: python gui.py
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import time
import math
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jarvis.config import config
from jarvis.assistant import JarvisAssistant
from jarvis.memory import get_memory
from jarvis.utils import logger

class ArcReactorCanvas(tk.Canvas):
    """Animated arc reactor like JARVIS"""
    def __init__(self, parent, size=200, **kwargs):
        super().__init__(parent, width=size, height=size, bg='#0a0f1c', highlightthickness=0, **kwargs)
        self.size = size
        self.center = size // 2
        self.angle = 0
        self.pulse = 0
        self.speaking = False
        self._animate()

    def set_speaking(self, speaking: bool):
        self.speaking = speaking

    def _animate(self):
        self.delete("all")
        
        # Background glow
        for i in range(5):
            radius = 30 + i*15 + (math.sin(self.pulse)*5 if self.speaking else 0)
            intensity = 0.2 - i*0.03
            color = self._hex_intensity('#00d4ff', intensity)
            self.create_oval(
                self.center - radius, self.center - radius,
                self.center + radius, self.center + radius,
                outline=color, width=2
            )

        # Outer ring
        self.create_oval(
            self.center-80, self.center-80,
            self.center+80, self.center+80,
            outline='#00aaff', width=3
        )
        
        # Rotating segments
        for i in range(3):
            a = self.angle + i*120
            x1 = self.center + 50 * math.cos(math.radians(a))
            y1 = self.center + 50 * math.sin(math.radians(a))
            x2 = self.center + 70 * math.cos(math.radians(a+20))
            y2 = self.center + 70 * math.sin(math.radians(a+20))
            self.create_line(x1, y1, x2, y2, fill='#00ffff', width=4, capstyle=tk.ROUND)

        # Inner core - pulsing when speaking
        core_radius = 25 + (math.sin(self.pulse * 2) * 8 if self.speaking else math.sin(self.pulse)*2)
        core_color = '#ffffff' if self.speaking else '#aaffff'
        self.create_oval(
            self.center-core_radius, self.center-core_radius,
            self.center+core_radius, self.center+core_radius,
            fill=core_color, outline='#00d4ff', width=2
        )

        # Waveform around if speaking
        if self.speaking:
            for i in range(12):
                ang = i * 30 + self.angle*0.5
                h = random_wave = 10 + abs(math.sin(self.pulse + i))*15
                x = self.center + 85 * math.cos(math.radians(ang))
                y = self.center + 85 * math.sin(math.radians(ang))
                x2 = self.center + (85+h) * math.cos(math.radians(ang))
                y2 = self.center + (85+h) * math.sin(math.radians(ang))
                self.create_line(x, y, x2, y2, fill='#00ffaa', width=2)

        self.angle = (self.angle + (3 if self.speaking else 1)) % 360
        self.pulse += 0.15 if self.speaking else 0.05
        
        self.after(50, self._animate)

    def _hex_intensity(self, hex_color, intensity):
        # Simple - return with lower intensity by darkening
        # For simplicity just return original with alpha simulation via darker color
        if intensity < 0.1:
            return '#0a2a3a'
        elif intensity < 0.15:
            return '#0a4a6a'
        else:
            return hex_color

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS - Just A Rather Very Intelligent System")
        self.root.geometry("1100x700")
        self.root.configure(bg='#0a0f1c')
        
        self.assistant = JarvisAssistant(text_mode=True)  # GUI uses text mode input but voice output
        self.memory = get_memory()
        self.is_listening = False
        self.listen_thread = None
        
        self.setup_ui()
        
        # Start reminder checker
        self.root.after(1000, self.update_status)
        
        # Welcome message
        self.add_message("JARVIS", f"Good {'morning' if datetime.datetime.now().hour < 12 else 'afternoon' if datetime.datetime.now().hour < 18 else 'evening'} Sir. Systems online. HUD initialized.")

    def setup_ui(self):
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', background='#1a2a4a', foreground='#00d4ff', font=('Consolas', 10))
        style.configure('TLabel', background='#0a0f1c', foreground='#aaffff')
        style.configure('TFrame', background='#0a0f1c')

        # Main containers
        header = tk.Frame(self.root, bg='#0a0f1c', height=60)
        header.pack(fill=tk.X, padx=10, pady=5)

        title = tk.Label(header, text="J.A.R.V.I.S", font=('Orbitron', 24, 'bold') if 'Orbitron' else ('Consolas', 24, 'bold'), fg='#00d4ff', bg='#0a0f1c')
        title.pack(side=tk.LEFT)
        
        subtitle = tk.Label(header, text="Just A Rather Very Intelligent System  •  v2.0  •  ONLINE", font=('Consolas', 10), fg='#5a7a8a', bg='#0a0f1c')
        subtitle.pack(side=tk.LEFT, padx=20)

        status_frame = tk.Frame(header, bg='#0a0f1c')
        status_frame.pack(side=tk.RIGHT)
        
        self.status_label = tk.Label(status_frame, text="● STANDBY", font=('Consolas', 11, 'bold'), fg='#00ff88', bg='#0a0f1c')
        self.status_label.pack()
        
        self.time_label = tk.Label(status_frame, text="", font=('Consolas', 9), fg='#7a9aaa', bg='#0a0f1c')
        self.time_label.pack()

        # Body: left = reactor + controls, middle = chat, right = system info
        body = tk.Frame(self.root, bg='#0a0f1c')
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel
        left = tk.Frame(body, bg='#0e1a2e', width=250, relief=tk.FLAT)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,5))
        left.pack_propagate(False)

        self.reactor = ArcReactorCanvas(left, size=220)
        self.reactor.pack(pady=15)

        # Controls
        ctrl_label = tk.Label(left, text="VOICE CONTROLS", font=('Consolas', 10, 'bold'), fg='#00d4ff', bg='#0e1a2e')
        ctrl_label.pack(pady=(10,5))

        btn_speak = tk.Button(left, text="🎤 START LISTENING", command=self.toggle_listening, bg='#1a3a5a', fg='#00ffff', font=('Consolas', 10, 'bold'), relief=tk.FLAT, padx=10, pady=8, activebackground='#2a5a8a')
        btn_speak.pack(fill=tk.X, padx=10, pady=2)
        self.listen_btn = btn_speak

        btn_clear = tk.Button(left, text="🗑 Clear Chat", command=self.clear_chat, bg='#1e2a3e', fg='#88aacc', font=('Consolas', 9), relief=tk.FLAT, pady=5)
        btn_clear.pack(fill=tk.X, padx=10, pady=2)

        btn_todo = tk.Button(left, text="📋 Show TODO", command=self.show_todo, bg='#1e2a3e', fg='#88aacc', font=('Consolas', 9), relief=tk.FLAT, pady=5)
        btn_todo.pack(fill=tk.X, padx=10, pady=2)

        # Skills quick buttons
        skills_label = tk.Label(left, text="QUICK ACTIONS", font=('Consolas', 10, 'bold'), fg='#00d4ff', bg='#0e1a2e')
        skills_label.pack(pady=(15,5))

        quick_actions = [
            ("🕒 Time", "what time is it"),
            ("🌤 Weather", "weather"),
            ("🌐 Google", "open google"),
            ("🎵 YouTube", "open youtube"),
            ("😂 Joke", "tell me a joke"),
            ("📸 Screenshot", "take screenshot"),
        ]
        
        for label, cmd in quick_actions:
            b = tk.Button(left, text=label, command=lambda c=cmd: self.send_command(c), bg='#162a4a', fg='#aaddff', font=('Consolas', 9), relief=tk.FLAT, pady=4, anchor='w', padx=10)
            b.pack(fill=tk.X, padx=10, pady=1)

        # Middle - chat
        mid = tk.Frame(body, bg='#0a0f1c')
        mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        chat_label = tk.Label(mid, text="CONVERSATION LOG", font=('Consolas', 10, 'bold'), fg='#00d4ff', bg='#0a0f1c', anchor='w')
        chat_label.pack(fill=tk.X)

        self.chat_display = scrolledtext.ScrolledText(mid, wrap=tk.WORD, font=('Consolas', 11), bg='#0e1a2e', fg='#cceeff', insertbackground='#00ffff', relief=tk.FLAT, padx=10, pady=10)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=5)
        self.chat_display.configure(state='disabled')

        # Input frame
        input_frame = tk.Frame(mid, bg='#0a0f1c')
        input_frame.pack(fill=tk.X, pady=(5,0))

        self.input_entry = tk.Entry(input_frame, font=('Consolas', 12), bg='#1a2a4a', fg='#ffffff', insertbackground='#00ffff', relief=tk.FLAT)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,5))
        self.input_entry.bind('<Return>', lambda e: self.send_from_entry())
        self.input_entry.focus()

        send_btn = tk.Button(input_frame, text="SEND ▶", command=self.send_from_entry, bg='#00aaff', fg='#ffffff', font=('Consolas', 10, 'bold'), relief=tk.FLAT, padx=15, pady=8, activebackground='#00d4ff')
        send_btn.pack(side=tk.RIGHT)

        # Right panel - system info
        right = tk.Frame(body, bg='#0e1a2e', width=220)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(5,0))
        right.pack_propagate(False)

        info_label = tk.Label(right, text="SYSTEM STATUS", font=('Consolas', 10, 'bold'), fg='#00d4ff', bg='#0e1a2e')
        info_label.pack(pady=10)

        self.sys_info = tk.Label(right, text="Loading...", font=('Consolas', 9), fg='#88aacc', bg='#0e1a2e', justify=tk.LEFT, anchor='nw')
        self.sys_info.pack(fill=tk.X, padx=10, pady=5, anchor='n')

        # Memory / stats
        mem_label = tk.Label(right, text="MEMORY", font=('Consolas', 10, 'bold'), fg='#00d4ff', bg='#0e1a2e')
        mem_label.pack(pady=(15,5))

        self.mem_info = scrolledtext.ScrolledText(right, height=10, font=('Consolas', 8), bg='#0a142a', fg='#7a9abb', relief=tk.FLAT, wrap=tk.WORD)
        self.mem_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Footer status
        footer = tk.Frame(self.root, bg='#081020', height=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self.footer_label = tk.Label(footer, text="JARVIS HUD Ready • Text mode • TTS Enabled", font=('Consolas', 8), fg='#5a7a8a', bg='#081020', anchor='w')
        self.footer_label.pack(side=tk.LEFT, padx=10)

    def add_message(self, sender, message):
        self.chat_display.configure(state='normal')
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if sender == "YOU":
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: ", "user_tag")
            self.chat_display.tag_config("user_tag", foreground="#00ff88", font=('Consolas', 10, 'bold'))
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: ", "jarvis_tag")
            self.chat_display.tag_config("jarvis_tag", foreground="#00d4ff", font=('Consolas', 10, 'bold'))
        
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

    def send_from_entry(self):
        text = self.input_entry.get().strip()
        if not text:
            return
        self.input_entry.delete(0, tk.END)
        self.send_command(text)

    def send_command(self, text):
        self.add_message("YOU", text)
        self.footer_label.config(text=f"Processing: {text}...")
        self.reactor.set_speaking(True)
        self.status_label.config(text="● THINKING", fg="#ffaa00")
        
        def process():
            try:
                response = self.assistant.brain.process(text)
                clean = response.replace("__EXIT__", "").strip()
                # Update UI in main thread
                self.root.after(0, lambda: self._on_response(clean))
            except Exception as e:
                logger.error(f"GUI process error: {e}")
                self.root.after(0, lambda: self._on_response(f"Error processing: {e}"))
        
        threading.Thread(target=process, daemon=True).start()

    def _on_response(self, response):
        self.add_message("JARVIS", response)
        self.reactor.set_speaking(False)
        self.status_label.config(text="● STANDBY", fg="#00ff88")
        self.footer_label.config(text="Ready")
        
        # Speak
        def speak():
            try:
                self.assistant.tts.speak(response)
            except Exception as e:
                logger.error(f"TTS error in GUI: {e}")
        
        threading.Thread(target=speak, daemon=True).start()
        
        # Update memory display
        self.update_memory_display()

    def toggle_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.listen_btn.config(text="⏹ STOP LISTENING", bg="#5a1a1a")
            self.status_label.config(text="● LISTENING", fg="#ff4444")
            self.reactor.set_speaking(True)
            
            def listen_loop():
                try:
                    self.add_message("SYSTEM", "Listening... Speak now (say 'exit' to stop)")
                    while self.is_listening:
                        text = self.assistant.stt.listen_once(timeout=3, phrase_time_limit=6)
                        if text and self.is_listening:
                            self.root.after(0, lambda t=text: self.send_command(t))
                except Exception as e:
                    logger.error(f"Listen loop error: {e}")
                finally:
                    self.root.after(0, self._stop_listening_ui)
            
            self.listen_thread = threading.Thread(target=listen_loop, daemon=True)
            self.listen_thread.start()
        else:
            self.is_listening = False
            self._stop_listening_ui()

    def _stop_listening_ui(self):
        self.is_listening = False
        self.listen_btn.config(text="🎤 START LISTENING", bg="#1a3a5a")
        self.status_label.config(text="● STANDBY", fg="#00ff88")
        self.reactor.set_speaking(False)

    def clear_chat(self):
        self.chat_display.configure(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.configure(state='disabled')
        self.add_message("SYSTEM", "Chat cleared")

    def show_todo(self):
        todos = self.memory.list_todo()
        if not todos:
            self.add_message("JARVIS", "Your todo list is empty, sir")
        else:
            msg = "Pending tasks:\n" + "\n".join([f"{i+1}. {t['task']}" for i, t in enumerate(todos)])
            self.add_message("JARVIS", msg)

    def update_status(self):
        # Update time
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=now)
        
        # Update sys info
        try:
            import psutil
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.sys_info.config(text=f"CPU: {cpu}%\nRAM: {ram}%\n\nMODE: TEXT+VOICE\nTTS: {config.TTS_ENGINE}\nVISION: {'ON' if config.ENABLE_VISION else 'OFF'}\n\nWake Words:\n" + "\n".join(config.WAKE_WORDS[:3]))
        except:
            self.sys_info.config(text=f"MODE: TEXT+VOICE\nTTS: {config.TTS_ENGINE}\nVISION: {'ON' if config.ENABLE_VISION else 'OFF'}")
        
        self.root.after(1000, self.update_status)

    def update_memory_display(self):
        try:
            hist = self.memory.get_history(5)
            text = f"Conversations: {len(self.memory.data.get('history',[]))}\n"
            text += f"TODO: {len(self.memory.list_todo())}\n"
            text += f"Reminders: {len([r for r in self.memory.data.get('reminders',[]) if not r.get('triggered')])}\n\n"
            text += "Recent:\n"
            for h in hist[-3:]:
                text += f"U: {h['user'][:30]}...\n"
            self.mem_info.delete(1.0, tk.END)
            self.mem_info.insert(tk.END, text)
        except Exception as e:
            pass

    def on_close(self):
        self.is_listening = False
        self.assistant.shutdown()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
