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

import numpy as np
import pyaudio
import pygame
import pyttsx3
import requests
import speech_recognition as sr
import sv_ttk
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import wikipedia

# --------------------------------------------------
# 📝 Configuration and Setup
# --------------------------------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Loads configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        default_config = {
            "USER_NAME": "User", "VOICE_ID": 1, "SPEECH_RATE": 180,
            "THEME": "dark", "SOUND_EFFECTS": True, "VISUALIZER": True
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    except json.JSONDecodeError:
        logging.error("Error decoding config.json. Please check its format.")
        sys.exit(1)

CONFIG = load_config()
DEEPSEEK_API_KEY = os.getenv("")

pygame.mixer.init()
SOUNDS = {
    "startup": "sounds/startup.wav", "notification": "sounds/notification.wav",
    "success": "sounds/success.wav", "error": "sounds/error.wav"
}

# --------------------------------------------------
# 🎤 Audio Visualizer (Lightweight Tkinter version)
# --------------------------------------------------
class AudioVisualizer(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg="#1c1c1c", highlightthickness=0)
        self.num_bars = 30
        self.bars = []
        self.bar_width = (int(self["width"]) - 20) / self.num_bars
        for i in range(self.num_bars):
            x0 = i * self.bar_width + 10
            bar = self.create_rectangle(x0, int(self["height"]), x0 + self.bar_width - 2, int(self["height"]), fill="#00ff99", outline="")
            self.bars.append(bar)

    def update_visualizer(self, rms_volume):
        if not CONFIG["VISUALIZER"]: return
        max_height = int(self["height"])
        for i, bar in enumerate(self.bars):
            sine_mod = (np.sin(i / 1.5 + time.time() * 10) + 1) / 2
            bar_height = max(2, rms_volume * max_height * sine_mod * 15)
            y0 = max_height - bar_height
            self.coords(bar, self.coords(bar)[0], y0, self.coords(bar)[2], max_height)
            color_intensity = int(min(255, bar_height / max_height * 255 * 1.5))
            color = f'#{color_intensity:02x}{255-color_intensity:02x}99'
            self.itemconfig(bar, fill=color)

# --------------------------------------------------
# 🗣️ Voice Engine
# --------------------------------------------------
class VoiceEngine:
    def __init__(self, visualizer):
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.audio_visualizer = visualizer
        self.is_listening = False
        voices = self.engine.getProperty('voices')
        if 0 <= CONFIG["VOICE_ID"] < len(voices):
            self.engine.setProperty('voice', voices[CONFIG["VOICE_ID"]].id)
        self.engine.setProperty('rate', CONFIG["SPEECH_RATE"])
    
    def speak(self, text):
        logging.info(f"Dazzy says: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except RuntimeError as e:
            logging.error(f"Speech engine error: {e}. This can happen during shutdown.")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        try:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
            if self.audio_visualizer:
                self.audio_visualizer.after(0, self.audio_visualizer.update_visualizer, rms / 1000)
        except Exception as e:
            logging.warning(f"Audio callback error: {e}")
        return (in_data, pyaudio.paContinue)

    def listen(self):
        p = pyaudio.PyAudio()
        stream = None
        with sr.Microphone() as source:
            self.is_listening = True
            logging.info("Listening for your command...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            if CONFIG["VISUALIZER"] and self.audio_visualizer:
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                                input=True, frames_per_buffer=1024,
                                stream_callback=self._audio_callback)
                stream.start_stream()
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                if CONFIG["SOUND_EFFECTS"]:
                    self.play_sound_local("notification")
                text = self.recognizer.recognize_google(audio)
                logging.info(f"You said: {text}")
                return text.lower()
            except sr.UnknownValueError:
                logging.warning("Could not understand audio.")
                return ""
            except sr.RequestError as e:
                logging.error(f"Could not request results from Google; {e}")
                return ""
            except Exception as e:
                logging.error(f"An error occurred during listening: {e}")
                return ""
            finally:
                self.is_listening = False
                if stream and stream.is_active():
                    stream.stop_stream()
                    stream.close()
                p.terminate()

    def play_sound_local(self, sound_type):
        try:
            sound_path = SOUNDS.get(sound_type)
            if sound_path and os.path.exists(sound_path):
                pygame.mixer.Sound(sound_path).play()
            else:
                logging.warning(f"Sound file not found: {sound_path}")
        except Exception as e:
            logging.error(f"Error playing sound: {e}")

# --------------------------------------------------
# 🤖 AI Assistant Core Logic
# --------------------------------------------------
class DazzyAssistant:
    def __init__(self, voice_engine):
        self.voice_engine = voice_engine
        self.user_name = CONFIG["USER_NAME"]
        
        self.command_map = {
            "hello": self.greet, "hi": self.greet, "hey": self.greet,
            "goodbye": self.farewell, "bye": self.farewell, "exit": self.farewell,
            "open youtube": self.open_youtube, "open google": self.open_google,
            "open ChatGPT": self.open_ChatGPT, "open google": self.open_ChatGPT,
            "open github": self.open_github, # This command now has a corresponding method
            "search youtube for": self.search_youtube,
            "search google for": self.search_google, "search for": self.search_google,
            "who is": self.get_wikipedia_summary, "tell me about": self.get_wikipedia_summary,
            "the time": self.get_time, "the date": self.get_date,
            "tell me a joke": self.tell_joke,
            "calculate": self.calculate, "compute": self.calculate,
        }
        self.load_custom_commands()

    def load_custom_commands(self):
        try:
            with open('commands.json', 'r') as f:
                custom_commands = json.load(f)
                for command, url in custom_commands.get("websites", {}).items():
                    self.command_map[f"open {command}"] = lambda u=url: self.open_website(u)
        except FileNotFoundError:
            logging.warning("commands.json not found. Skipping custom commands.")
        except Exception as e:
            logging.error(f"Error loading commands.json: {e}")

    # --- Command Functions ---
    def open_website(self, url):
        webbrowser.open(url)
        return f"Opening {url}."

    def greet(self, _=""):
        return "Hello Nikhil Pandey"

    def farewell(self, _=""):
        return f"Goodbye, {self.user_name}! Have a great day."
        
    def open_youtube(self, _=""):
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."
        
def open_youtube(self, _=""):
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."
    
    def open_google(self, _=""):
        webbrowser.open("https://www.google.com")
        return "Opening Google."

    def open_instagram(self, _=""):
        webbrowser.open("https://www.instagram.com")
        return "Opening instagram."

    def open_car(self, _=""):
        webbrowser.open("https://www.car.com")
        return "Opening car."
        
    def open_ChatGPT(self, _=""):
        webbrowser.open("https://chatgpt.com/")
        return "Opening ChatGPT."

def open_Gla(self, _=""):
        webbrowser.open("https://glauniversity.in:8085/#")
        return "Opening Gla."

    def open_Word(self, _=""):
        webbrowser.open("https://word.com/")
        return "Opening Word."

    def open_Canva(self, _=""):
        webbrowser.open("https://www.canva.com/features/cutout-image/")
        return "Opening Canva."

    def open_gamma ai(self, _=""):
        webbrowser.open("https://gamma.app/")
        return "Opening gamma ai."

    def open_Gemini(self, _=""):
        webbrowser.open("https://gemini.google.com/")
        return "Opening Gemini."

 def open_Googlemeet(self, _=""):
        webbrowser.open("https://meet.google.com/")
        return "Opening Google meet."

    # FIXED: Added the missing open_github method
    def open_github(self, _=""):
        webbrowser.open("https://www.github.com")
        return "Opening GitHub."
        
        def open_Spotify(self, _=""):
        webbrowser.open("https://open.spotify.com/")
        return "Opening Spotify."

    def search_youtube(self, query):
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching YouTube for {query}."

    def search_google(self, query):
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching Google for {query}."

    def get_wikipedia_summary(self, query):
        try:
            # Try to get the exact page first
            page = wikipedia.page(query, auto_suggest=False)
            # If the returned page title is not the same as the query, ask for clarification
            if page.title.lower() != query.strip().lower():
                return f"I found '{page.title}' instead of '{query}'. Did you mean '{page.title}'? Please clarify."
            summary = page.summary.split('\n')[0]
            if "may refer to:" in summary.lower():
                return f"'{query}' may refer to multiple things. Can you be more specific?"
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            return f"'{query}' is ambiguous. Did you mean: {', '.join(e.options[:3])}?"
        except wikipedia.exceptions.PageError:
            return f"Sorry, I couldn't find any information on Wikipedia for '{query}'."
        except Exception as e:
            logging.error(f"Wikipedia error: {e}")
            return "Sorry, I'm having trouble connecting to Wikipedia right now."

    def get_time(self, _=""):
        return f"The current time is {datetime.now().strftime('%I:%M %p')}."

    def get_date(self, _=""):
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

    def tell_joke(self, _=""):
        return random.choice([
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she should embrace her mistakes. She gave me a hug.",
            "Why did the scarecrow win an award? Because he was outstanding in his field!"
        ])
    
    def calculate(self, query):
        try:
            query = query.lower().replace('x', '*').replace('times', '*').replace('divided by', '/').replace('plus', '+').replace('minus', '-')
            match = re.search(r'(\d+\.?\d*)\s*([+\-*/])\s*(\d+\.?\d*)', query)
            if not match:
                return "I couldn't understand the calculation. Please state it clearly, like '5 times 3'."
            num1, op, num2 = float(match.group(1)), match.group(2), float(match.group(3))
            
            if op == '+': result = num1 + num2
            elif op == '-': result = num1 - num2
            elif op == '*': result = num1 * num2
            elif op == '/':
                if num2 == 0: return "I can't divide by zero."
                result = num1 / num2
            else: return "Unknown operator."
            return f"The answer is {int(result) if result.is_integer() else round(result, 4)}."
        except Exception as e:
            logging.error(f"Calculation error: {e}")
            return "Sorry, I had trouble with that calculation."

    def ask_deepseek(self, prompt):
        if not DEEPSEEK_API_KEY: return "API key not configured. I can only handle built-in commands."
        url, headers = "https://api.deepseek.com/v1/chat/completions", {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "deepseek-chat", "messages": [{"role": "system", "content": f"You are Dazzy, a friendly AI assistant."}, {"role": "user", "content": prompt}]}
        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            return f"An HTTP error occurred: {e}"
        except Exception as e:
            logging.error(f"API request failed: {e}")
            return "I'm having trouble connecting to my brain right now."

    def handle_command(self, command):
        cmd_lower = command.lower().strip()
        # --- NEW: Handle plain math expressions like "3+4" or "12 / 6" ---
        if re.fullmatch(r'\s*-?\d+(\.\d+)?\s*[\+\-\*/]\s*-?\d+(\.\d+)?\s*', cmd_lower):
            try:
                result = eval(cmd_lower)
                return f"The answer is {int(result) if isinstance(result, float) and result.is_integer() else round(result, 4)}."
            except Exception:
                return "Sorry, I couldn't calculate that expression."
        # --- rest of your code ---
        # Math intent detection
        if cmd_lower.startswith("add "):
            nums = re.findall(r'-?\d+\.?\d*', cmd_lower)
            if len(nums) >= 2:
                result = sum(float(n) for n in nums)
                return f"The answer is {int(result) if result.is_integer() else round(result, 4)}."
            else:
                return "Please provide at least two numbers to add."
        if cmd_lower.startswith("subtract "):
            nums = re.findall(r'-?\d+\.?\d*', cmd_lower)
            if len(nums) >= 2:
                result = float(nums[0])
                for n in nums[1:]:
                    result -= float(n)
                return f"The answer is {int(result) if result.is_integer() else round(result, 4)}."
            else:
                return "Please provide at least two numbers to subtract."
        if cmd_lower.startswith("multiply "):
            nums = re.findall(r'-?\d+\.?\d*', cmd_lower)
            if len(nums) >= 2:
                result = float(nums[0])
                for n in nums[1:]:
                    result *= float(n)
                return f"The answer is {int(result) if result.is_integer() else round(result, 4)}."
            else:
                return "Please provide at least two numbers to multiply."
        if cmd_lower.startswith("divide "):
            nums = re.findall(r'-?\d+\.?\d*', cmd_lower)
            if len(nums) >= 2:
                result = float(nums[0])
                try:
                    for n in nums[1:]:
                        if float(n) == 0:
                            return "I can't divide by zero."
                        result /= float(n)
                except Exception:
                    return "There was an error dividing the numbers."
                return f"The answer is {int(result) if result.is_integer() else round(result, 4)}."
            else:
                return "Please provide at least two numbers to divide."
        # Existing logic
        if cmd_lower.startswith("what is"):
            if re.search(r'\d', cmd_lower): return self.calculate(cmd_lower)
            else: return self.get_wikipedia_summary(cmd_lower.replace("what is", "").strip())
        for key, func in self.command_map.items():
            if cmd_lower.startswith(key):
                return func(cmd_lower[len(key):].strip())
        return self.ask_deepseek(command)

# --------------------------------------------------
# 🖥️ Graphical User Interface (GUI)
# --------------------------------------------------
class DazzyUI:
    def __init__(self, root, assistant):
        self.root, self.assistant = root, assistant
        self.setup_ui()
        self.play_sound("startup")

    def setup_ui(self):
        self.root.title(f"Dazzy AI Assistant - {CONFIG['USER_NAME']}")
        self.root.geometry("800x700"), self.root.minsize(600, 500)
        sv_ttk.set_theme(CONFIG["THEME"])
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        self.logo_label = ttk.Label(header_frame, text="✨", font=("Segoe UI", 24))
        self.logo_label.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(header_frame, text="Dazzy AI", font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)

        self.conversation = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=("Segoe UI", 12), state='disabled', padx=10, pady=10)
        self.conversation.pack(fill=tk.BOTH, expand=True)

        if CONFIG["VISUALIZER"]:
            self.visualizer = AudioVisualizer(main_frame, width=800, height=80)
            self.visualizer.pack(fill=tk.X, pady=5)
            self.assistant.voice_engine.audio_visualizer = self.visualizer

        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        input_frame.columnconfigure(0, weight=1)

        self.user_input = ttk.Entry(input_frame, font=("Segoe UI", 12))
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.user_input.bind("<Return>", self.on_send)
        self.voice_btn = ttk.Button(input_frame, text="🎤", command=self.on_voice)
        self.voice_btn.grid(row=0, column=2)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=2).pack(side=tk.BOTTOM, fill=tk.X)
        self.add_message("Dazzy", self.assistant.greet())
        
    def play_sound(self, sound_type):
        if CONFIG["SOUND_EFFECTS"]:
            self.assistant.voice_engine.play_sound_local(sound_type)

    def add_message(self, sender, message):
        self.conversation.config(state='normal')
        self.conversation.insert(tk.END, f"{sender}:\n", ("sender",))
        self.conversation.insert(tk.END, f"{message}\n\n")
        self.conversation.config(state='disabled')
        self.conversation.see(tk.END)
        self.conversation.tag_config("sender", font=("Segoe UI", 12, "bold"))

    def on_send(self, event=None):
        user_text = self.user_input.get().strip()
        if user_text:
            self.add_message(self.assistant.user_name, user_text)
            self.user_input.delete(0, tk.END)
            threading.Thread(target=self.process_command, args=(user_text,), daemon=True).start()

    def on_voice(self):
        self.voice_btn.config(state="disabled")
        self.status_var.set("Listening..."), self.logo_label.config(text="🎙️")
        self.play_sound("notification")
        threading.Thread(target=self.listen_thread, daemon=True).start()

    def listen_thread(self):
        command = self.assistant.voice_engine.listen()
        def update_ui():
            self.voice_btn.config(state="normal")
            self.status_var.set("Ready"), self.logo_label.config(text="✨")
            if command:
                self.add_message(self.assistant.user_name, command)
                self.process_command(command)
        self.root.after(0, update_ui)
    
    def process_command(self, command):
        self.status_var.set("Thinking...")
        try:
            response = self.assistant.handle_command(command)
            self.play_sound("success")
        except Exception as e:
            response, _ = f"An unexpected error occurred: {e}", self.play_sound("error")
            logging.error(f"Error handling command '{command}': {e}")
        def update_and_speak():
            self.add_message("Dazzy", response)
            self.status_var.set("Ready")
            threading.Thread(target=self.assistant.voice_engine.speak, args=(response,), daemon=True).start()
            if any(farewell in command.lower() for farewell in ["bye", "goodbye", "exit"]):
                self.root.after(2000, self.root.destroy)
        self.root.after(0, update_and_speak)

# --------------------------------------------------
# 🚀 Main Application Execution
# --------------------------------------------------
def main():
    if not DEEPSEEK_API_KEY:
        logging.warning("DEEPSEEK_API_KEY environment variable not set. API features will be disabled.")
    
    root = tk.Tk()
    try:
        if sys.platform.startswith('win'): root.iconbitmap("icon.ico")
    except tk.TclError:
        logging.warning("icon.ico not found. Skipping icon setting.")
    
    voice_engine = VoiceEngine(None) # Visualizer is set later
    assistant = DazzyAssistant(voice_engine)
    DazzyUI(root, assistant)
    
    # FIXED: Simplified on_closing to prevent RuntimeError
    def on_closing():
        """Handles the window closing event."""
        logging.info("Application closing.")
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
