import os
import json
import random
import threading
import webbrowser
import logging
from datetime import datetime

import requests
import wikipedia
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox

# --------------------------------------------------
# 🌱 Environment & Config
# --------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Enhanced Professional Color Palette
BG_MAIN = "#0f111a"      # Deep obsidian background
BG_SIDEBAR = "#1a1c25"   # Dark slate sidebar
BG_CHAT = "#13151f"      # Chat area background
FG_TEXT = "#e1e1e6"      # Soft white text
ACCENT_BLUE = "#5865f2"  # Vibrant Blurple (Discord-esque)
USER_COLOR = "#00d2ff"   # Electric Cyan for user
AI_COLOR = "#bb86fc"     # Soft Purple for AI
STATUS_GREEN = "#43b581" # Success green
STATUS_BUSY = "#faa61a"  # Warning orange

# --------------------------------------------------
# 🤖 Assistant Logic
# --------------------------------------------------
class DazzyAssistant:
    def __init__(self):
        self.user_name = "User"

    def handle_command(self, text):
        cmd = text.lower().strip()
        
        # Simple Logic Map
        if any(greet in cmd for greet in ["hello", "hi", "hey"]):
            return f"Hello! I'm Dazzy. How can I brighten your day today?"
        elif "time" in cmd:
            return datetime.now().strftime("It's currently %I:%M %p.")
        elif "date" in cmd:
            return datetime.now().strftime("Today's date is %A, %B %d, %Y.")
        elif "open youtube" in cmd:
            webbrowser.open("https://youtube.com")
            return "Sure thing! Launching YouTube now."
        elif "who is" in cmd or "what is" in cmd:
            try:
                topic = cmd.replace("who is", "").replace("what is", "").strip()
                return wikipedia.summary(topic, sentences=2)
            except:
                return "I couldn't find a clear Wikipedia entry for that. Should I search deeper?"
        
        # Fallback to DeepSeek
        return self.ask_deepseek(text)

    def ask_deepseek(self, prompt):
        if not DEEPSEEK_API_KEY:
            return "I'm currently in offline mode because the DeepSeek API key is missing. Please add it to your .env file!"
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"I ran into a connection issue with DeepSeek: {str(e)}"

# --------------------------------------------------
# 🖥️ Modern UI Class
# --------------------------------------------------
class ModernAssistantUI:
    def __init__(self, root):
        self.root = root
        self.assistant = DazzyAssistant()
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        self.root.title("Dazzy AI")
        self.root.geometry("1000x700")
        self.root.configure(bg=BG_MAIN)
        
    def create_widgets(self):
        # --- Layout Grid ---
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=240)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)
        
        # Sidebar Logo/Header
        lbl_logo = tk.Label(self.sidebar, text="✧", bg=BG_SIDEBAR, fg=ACCENT_BLUE, 
                            font=("Segoe UI", 32))
        lbl_logo.pack(pady=(40, 0))
        
        lbl_title = tk.Label(self.sidebar, text="DAZZY AI", bg=BG_SIDEBAR, fg="white", 
                             font=("Segoe UI Semibold", 16), pady=10)
        lbl_title.pack()

        # Separator Line
        line = tk.Frame(self.sidebar, bg="#2d2f3b", height=1, width=180)
        line.pack(pady=20)

        # Status Panel
        self.status_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        self.status_frame.pack(pady=20)

        self.status_circle = tk.Canvas(self.status_frame, width=12, height=12, bg=BG_SIDEBAR, highlightthickness=0)
        self.status_circle.pack(side=tk.LEFT, padx=10)
        self.status_dot = self.status_circle.create_oval(2, 2, 10, 10, fill=STATUS_GREEN, outline="")
        
        self.lbl_status = tk.Label(self.status_frame, text="ONLINE", bg=BG_SIDEBAR, fg="#a0a0a0", 
                                   font=("Segoe UI Bold", 8))
        self.lbl_status.pack(side=tk.LEFT)

        # --- Chat Area ---
        self.main_container = tk.Frame(self.root, bg=BG_MAIN)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        # Shadow Effect Frame for Chat
        self.chat_shadow = tk.Frame(self.main_container, bg="#1a1c25", padx=1, pady=1)
        self.chat_shadow.pack(expand=True, fill=tk.BOTH, pady=(0, 20))

        self.chat_display = scrolledtext.ScrolledText(
            self.chat_shadow, wrap=tk.WORD, bg=BG_CHAT, fg=FG_TEXT,
            font=("Segoe UI", 11), padx=20, pady=20, borderwidth=0, 
            highlightthickness=0, insertbackground="white"
        )
        self.chat_display.pack(expand=True, fill=tk.BOTH)
        
        # Stylish Tags
        self.chat_display.tag_configure("user_header", foreground=USER_COLOR, font=("Segoe UI Bold", 10))
        self.chat_display.tag_configure("ai_header", foreground=AI_COLOR, font=("Segoe UI Bold", 10))
        self.chat_display.tag_configure("system", foreground="#5c5e6d", font=("Segoe UI Italic", 9))
        self.chat_display.tag_configure("message_body", spacing1=5, spacing3=15)

        # --- Input Bar ---
        self.input_container = tk.Frame(self.main_container, bg=BG_MAIN)
        self.input_container.pack(fill=tk.X)
        
        # Rounded-look entry
        self.entry_frame = tk.Frame(self.input_container, bg="#252733", padx=15, pady=5)
        self.entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.entry = tk.Entry(
            self.entry_frame, bg="#252733", fg="white", insertbackground="white",
            font=("Segoe UI", 12), borderwidth=0, highlightthickness=0
        )
        self.entry.pack(fill=tk.X, ipady=8)
        self.entry.bind("<Return>", self.start_send_thread)

        # Stylish Send Button
        self.btn_send = tk.Button(
            self.input_container, text="✦", bg=ACCENT_BLUE, fg="white", 
            activebackground="#4752c4", activeforeground="white",
            font=("Segoe UI", 14), borderwidth=0, padx=25, cursor="hand2",
            command=self.start_send_thread
        )
        self.btn_send.pack(side=tk.RIGHT, padx=(15, 0))

        self.append_message("System", "Neural link established. Dazzy is ready.", "system")

    def append_message(self, sender, message, tag):
        self.chat_display.config(state=tk.NORMAL)
        
        if sender == "You":
            header_tag = "user_header"
        elif sender == "Dazzy":
            header_tag = "ai_header"
        else:
            header_tag = "system"

        self.chat_display.insert(tk.END, f"{sender.upper()}\n", header_tag)
        self.chat_display.insert(tk.END, f"{message}\n", "message_body")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def set_busy(self, is_busy):
        if is_busy:
            self.status_circle.itemconfig(self.status_dot, fill=STATUS_BUSY)
            self.lbl_status.config(text="THINKING", fg=STATUS_BUSY)
            self.btn_send.config(state=tk.DISABLED, bg="#3b405a")
        else:
            self.status_circle.itemconfig(self.status_dot, fill=STATUS_GREEN)
            self.lbl_status.config(text="ONLINE", fg="#a0a0a0")
            self.btn_send.config(state=tk.NORMAL, bg=ACCENT_BLUE)

    def start_send_thread(self, event=None):
        user_text = self.entry.get().strip()
        if not user_text:
            return
        
        self.entry.delete(0, tk.END)
        self.append_message("You", user_text, "user_tag")
        
        self.set_busy(True)
        thread = threading.Thread(target=self.process_response, args=(user_text,))
        thread.daemon = True
        thread.start()

    def process_response(self, text):
        response = self.assistant.handle_command(text)
        self.root.after(0, lambda: self.append_message("Dazzy", response, "ai_tag"))
        self.root.after(0, lambda: self.set_busy(False))

# --------------------------------------------------
# 🚀 Execution
# --------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    # High DPI support for clearer text on modern screens
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = ModernAssistantUI(root)
    root.mainloop()
