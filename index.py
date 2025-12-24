import os
import sys
import json
import random
import re
import threading
import time
import webbrowser
from datetime import datetime
import logging

import requests
import wikipedia
import tkinter as tk
from tkinter import scrolledtext, ttk

# --------------------------------------------------
# 🌱 Environment Variables (Local + Render Safe)
# --------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# --------------------------------------------------
# 📝 Configuration
# --------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "USER_NAME": "User",
            "THEME": "dark"
        }

CONFIG = load_config()

# --------------------------------------------------
# 🤖 Assistant Core
# --------------------------------------------------

class DazzyAssistant:
    def __init__(self):
        self.user_name = CONFIG["USER_NAME"]

        self.command_map = {
            "hello": self.greet,
            "hi": self.greet,
            "bye": self.farewell,
            "open youtube": lambda _: self.open_site("https://youtube.com"),
            "open google": lambda _: self.open_site("https://google.com"),
            "open github": lambda _: self.open_site("https://github.com"),
            "open chatgpt": lambda _: self.open_site("https://chatgpt.com"),
            "time": self.get_time,
            "date": self.get_date,
            "joke": self.tell_joke,
            "who is": self.wikipedia_search,
            "what is": self.wikipedia_search,
        }

    def greet(self, _=""):
        return f"Hello {self.user_name}"

    def farewell(self, _=""):
        return "Goodbye. Shutting down."

    def open_site(self, url):
        webbrowser.open(url)
        return f"Opening {url}"

    def get_time(self, _=""):
        return datetime.now().strftime("Time: %I:%M %p")

    def get_date(self, _=""):
        return datetime.now().strftime("Date: %A, %d %B %Y")

    def tell_joke(self, _=""):
        return random.choice([
            "Why do programmers hate nature? Too many bugs.",
            "I told my code a joke. It didn’t compile.",
            "Debugging is like being a detective in a crime movie where you are also the murderer."
        ])

    def wikipedia_search(self, query):
        try:
            return wikipedia.summary(query, sentences=1)
        except Exception:
            return "I couldn't find that on Wikipedia."

    def ask_deepseek(self, prompt):
        if not DEEPSEEK_API_KEY:
            return "DeepSeek API key not configured."

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            r = requests.post(url, headers=headers, json=data, timeout=15)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(e)
            return "DeepSeek is unavailable."

    def handle(self, command):
        cmd = command.lower().strip()

        for key, func in self.command_map.items():
            if cmd.startswith(key):
                return func(cmd.replace(key, "").strip())

        return self.ask_deepseek(command)

# --------------------------------------------------
# 🖥️ GUI (LOCAL ONLY)
# --------------------------------------------------

class DazzyUI:
    def __init__(self, root):
        self.assistant = DazzyAssistant()
        self.root = root
        self.root.title("Dazzy AI")

        self.chat = scrolledtext.ScrolledText(root, font=("Segoe UI", 12))
        self.chat.pack(expand=True, fill=tk.BOTH)

        self.entry = ttk.Entry(root)
        self.entry.pack(fill=tk.X)
        self.entry.bind("<Return>", self.send)

        self.write("Dazzy", self.assistant.greet())

    def write(self, sender, msg):
        self.chat.insert(tk.END, f"{sender}: {msg}\n")
        self.chat.see(tk.END)

    def send(self, event=None):
        text = self.entry.get()
        self.entry.delete(0, tk.END)
        self.write("You", text)

        response = self.assistant.handle(text)
        self.write("Dazzy", response)

# --------------------------------------------------
# 🚀 Run
# --------------------------------------------------

def main():
    if not DEEPSEEK_API_KEY:
        logging.warning("DeepSeek API key not set.")

    root = tk.Tk()
    DazzyUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
