import speech_recognition as sr
import pyttsx3
import webbrowser
import wikipedia
import requests
from googletrans import Translator
import os
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import json
import random
from PIL import Image, ImageTk
import sv_ttk
import pygame
from datetime import datetime
import math
import wave
import pyaudio
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# 🔐 Configuration
CONFIG = {
    "DEEPSEEK_API_KEY": "",  # Set to None to use local responses or add a valid key
    "USER_NAME": "Nikhil Pandey",  # Added personalized user name
    "VOICE_ID": 1,          # 0 for male, 1 for female voice
    "SPEECH_RATE": 170,
    "THEME": "dark",        # 'dark' or 'light'
    "ANIMATIONS": True,
    "SOUND_EFFECTS": True,
    "VISUALIZER": True,
    "USE_LOCAL_RESPONSES": True  # Fallback when API is not available
}

# 🎵 Initialize sound mixer
pygame.mixer.init()
SOUNDS = {
    "startup": "sounds/startup.wav",
    "notification": "sounds/notification.wav",
    "success": "sounds/success.wav",
    "error": "sounds/error.wav"
}

# 🎙️ Audio Visualizer
class AudioVisualizer:
    def __init__(self, root, width=300, height=100):
        self.root = root
        self.width = width
        self.height = height
        self.fig = Figure(figsize=(width/100, height/100), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1a1a2e')
        self.fig.patch.set_facecolor('#1a1a2e')
        self.line, = self.ax.plot([], [], color='#e94560', linewidth=2)
        self.ax.set_ylim(-1, 1)
        self.ax.set_xlim(0, 100)
        self.ax.axis('off')
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().config(bg='#1a1a2e')
        self.animation = None
        self.data = np.zeros(100)
        
    def update(self, audio_data):
        if not CONFIG["VISUALIZER"]:
            return
            
        self.data = np.roll(self.data, -1)
        self.data[-1] = audio_data
        self.line.set_data(np.arange(100), self.data)
        self.canvas.draw()
        
    def pack(self, **kwargs):
        self.canvas.get_tk_widget().pack(**kwargs)

# 🎤 Voice Engine
class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.voices = self.engine.getProperty('voices')
        self.set_voice(CONFIG["VOICE_ID"])
        self.engine.setProperty('rate', CONFIG["SPEECH_RATE"])
        self.is_listening = False
        self.audio_visualizer = None
        self.audio_stream = None
        
    def set_voice(self, voice_id):
        if 0 <= voice_id < len(self.voices):
            self.engine.setProperty('voice', self.voices[voice_id].id)
            
    def speak(self, text):
        print(f"\n🎙️ Dazzy says: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        
    def listen(self):
        with sr.Microphone() as source:
            self.is_listening = True
            print("\n🎤 Listening for your command...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Start audio stream for visualization
            if CONFIG["VISUALIZER"]:
                self.start_audio_stream()
                
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                
                if CONFIG["SOUND_EFFECTS"]:
                    pygame.mixer.Sound(SOUNDS["notification"]).play()
                    
                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"👂 You said: {text}")
                    return text.lower()
                except sr.UnknownValueError:
                    print("❌ Could not understand audio")
                    return ""
                except sr.RequestError as e:
                    print(f"❌ Could not request results; {e}")
                    return ""
            except Exception as e:
                print(f"❌ Error: {e}")
                return ""
            finally:
                self.is_listening = False
                if CONFIG["VISUALIZER"] and self.audio_stream:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                    
    def start_audio_stream(self):
        p = pyaudio.PyAudio()
        self.audio_stream = p.open(format=pyaudio.paInt16,
                                 channels=1,
                                 rate=44100,
                                 input=True,
                                 frames_per_buffer=1024,
                                 stream_callback=self.audio_callback)
        self.audio_stream.start_stream()
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.audio_visualizer and self.is_listening:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            if len(audio_data) > 0:
                normalized = audio_data / 32768.0
                self.audio_visualizer.update(normalized[0])
        return (in_data, pyaudio.paContinue)

# 🤖 AI Assistant Core
class DazzyAssistant:
    def __init__(self):
        self.voice_engine = VoiceEngine()
        self.command_history = []
        self.current_html_file = None
        self.load_commands()
        self.user_name = CONFIG["USER_NAME"]
        
    def load_commands(self):
        try:
            with open('commands.json', 'r') as f:
                self.custom_commands = json.load(f)
        except:
            self.custom_commands = {
                "greetings": ["hello", "hi", "hey", "greetings"],
                "farewells": ["bye", "goodbye", "exit", "see you"],
                "actions": {
                    "open youtube": "webbrowser.open('https://www.youtube.com')",
                    "open google": "webbrowser.open('https://www.google.com')",
                    "open github": "webbrowser.open('https://www.github.com')"
                }
            }
            
    def ask_dazzy(self, prompt):
        # If no API key or using local responses
        if not CONFIG["DEEPSEEK_API_KEY"] or CONFIG["USE_LOCAL_RESPONSES"]:
            return self.local_response(prompt)
            
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {CONFIG['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": f"You are Dazzy, a smart multilingual voice assistant talking to {self.user_name}."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 402:
                return "I can't process that request right now. Please check your API subscription."
            return f"Sorry, I encountered an error: {str(e)}"
        except Exception as e:
            return self.local_response(prompt)
            
    def local_response(self, prompt):
        """Fallback responses when API is not available"""
        prompt_lower = prompt.lower()
        
        if any(q in prompt_lower for q in ["how are you", "how's it going"]):
            return f"I'm doing great, {self.user_name}! How about you?"
            
        elif "weather" in prompt_lower:
            return "I can't check the weather right now, but you might want to look outside!"
            
        elif "your name" in prompt_lower:
            return "I'm Dazzy, your personal AI assistant!"
            
        elif "thank" in prompt_lower:
            return f"You're welcome, {self.user_name}!"
            
        return "I'm not sure how to respond to that. Could you try asking differently?"
            
    def create_html_file(self, topic, html_code):
        try:
            if not os.path.exists("html_output"):
                os.makedirs("html_output")
                
            filename = f"html_output/{topic.replace(' ', '_')}_{int(time.time())}.html"
            with open(filename, "w", encoding="utf-8") as file:
                file.write(html_code)
            self.current_html_file = filename
            webbrowser.open('file://' + os.path.realpath(filename))
            return f"Created HTML page for {topic}."
        except Exception as e:
            return f"Error creating HTML file: {e}"
            
    def get_wikipedia_summary(self, query):
        try:
            return wikipedia.summary(query, sentences=3, auto_suggest=True)
        except wikipedia.DisambiguationError as e:
            return f"Multiple options found. Please be more specific."
        except wikipedia.PageError:
            return f"I couldn't find information about {query}."
        except Exception:
            return "Wikipedia is unavailable right now."
            
    def handle_command(self, command):
        cmd = command.lower().strip()
        self.command_history.append(cmd)
        
        # Check custom commands first
        for action, script in self.custom_commands["actions"].items():
            if action in cmd:
                try:
                    exec(script)
                    return f"Executed: {action}"
                except Exception as e:
                    return f"Error executing command: {e}"
        
        # Built-in commands
        if any(greeting in cmd for greeting in self.custom_commands["greetings"]):
            greetings = [
                f"Hello {self.user_name}!",
                f"Hi {self.user_name}! How can I help you today?",
                f"Hey {self.user_name}! What can I do for you?"
            ]
            return random.choice(greetings)
            
        elif any(farewell in cmd for farewell in self.custom_commands["farewells"]):
            farewells = [
                f"Goodbye {self.user_name}! Have a great day!",
                f"See you later {self.user_name}!",
                f"Bye {self.user_name}! Come back soon!"
            ]
            return random.choice(farewells)
            
        elif "open youtube" in cmd:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."
            
        elif "search youtube for" in cmd:
            query = cmd.split("search youtube for", 1)[1].strip()
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}."
            
        elif "search" in cmd or "google" in cmd:
            query = cmd.split("search", 1)[1] if "search" in cmd else cmd.split("google", 1)[1]
            query = query.strip()
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching Google for {query}."
            
        elif any(prefix in cmd for prefix in ["who is", "what is", "tell me about"]):
            topic = cmd.split(" ", 2)[2] if " " in cmd else cmd
            return self.get_wikipedia_summary(topic)
            
        elif "create html" in cmd:
            topic = cmd.replace("create html", "").strip()
            if not topic:
                return "Please specify what HTML page to create."
            response = self.ask_dazzy(f"Generate HTML for {topic}")
            if "<html" in response.lower():
                return self.create_html_file(topic, response)
            return "Failed to generate HTML."
            
        elif "time" in cmd:
            return f"It's {datetime.now().strftime('%I:%M %p')}."
            
        elif "date" in cmd:
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
            
        elif "joke" in cmd:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
                "Why don't skeletons fight each other? They don't have the guts!"
            ]
            return random.choice(jokes)
            
        elif "clear" in cmd or "reset" in cmd:
            return "Type 'clear' in the chat to reset the conversation."
            
        else:
            return self.ask_dazzy(cmd)

# 🖥️ Modern UI
class DazzyUI:
    def __init__(self, root, assistant):
        self.root = root
        self.assistant = assistant
        self.assistant.voice_engine.audio_visualizer = AudioVisualizer(root)
        self.setup_ui()
        self.play_sound("startup")
        
    def setup_ui(self):
        self.root.title(f"✨ Dazzy AI Assistant - {CONFIG['USER_NAME']}")
        self.root.geometry("800x700")
        self.root.minsize(600, 600)
        sv_ttk.set_theme(CONFIG["THEME"])
        
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header with animated icon
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.logo_label = ttk.Label(self.header_frame, text="✨", font=("Segoe UI", 24))
        self.logo_label.pack(side=tk.LEFT)
        
        self.title_label = ttk.Label(
            self.header_frame, 
            text=f"Dazzy AI Assistant - {CONFIG['USER_NAME']}", 
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Conversation area
        self.conversation_frame = ttk.Frame(self.main_frame)
        self.conversation_frame.pack(fill=tk.BOTH, expand=True)
        
        self.conversation = scrolledtext.ScrolledText(
            self.conversation_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            state='disabled',
            padx=10,
            pady=10
        )
        self.conversation.pack(fill=tk.BOTH, expand=True)
        
        # Audio visualizer
        if CONFIG["VISUALIZER"]:
            self.assistant.voice_engine.audio_visualizer.pack(fill=tk.X, pady=5)
        
        # Input area
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.user_input = ttk.Entry(
            self.input_frame,
            font=("Segoe UI", 12)
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", self.on_send)
        
        self.send_btn = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.on_send
        )
        self.send_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.voice_btn = ttk.Button(
            self.input_frame,
            text="🎤",
            command=self.on_voice
        )
        self.voice_btn.pack(side=tk.LEFT)
        
        # Clear button
        self.clear_btn = ttk.Button(
            self.input_frame,
            text="Clear",
            command=self.clear_conversation
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Animation for listening state
        self.listening = False
        self.animate_logo()
        
        # Initial greeting
        self.add_message("Dazzy", f"Hello {CONFIG['USER_NAME']}! I'm Dazzy, your AI assistant. How can I help you today?")
        
    def animate_logo(self):
        if self.listening:
            angle = math.sin(time.time() * 5) * 15
            self.logo_label.config(text=f"🎙️")
        else:
            self.logo_label.config(text="✨")
        self.root.after(100, self.animate_logo)
        
    def play_sound(self, sound_type):
        if CONFIG["SOUND_EFFECTS"] and sound_type in SOUNDS:
            try:
                pygame.mixer.Sound(SOUNDS[sound_type]).play()
            except:
                pass
                
    def add_message(self, sender, message):
        self.conversation.config(state='normal')
        self.conversation.insert(tk.END, f"{sender}: {message}\n\n")
        self.conversation.config(state='disabled')
        self.conversation.see(tk.END)
        
    def clear_conversation(self):
        self.conversation.config(state='normal')
        self.conversation.delete(1.0, tk.END)
        self.conversation.config(state='disabled')
        self.add_message("Dazzy", f"Conversation cleared. How can I help you, {CONFIG['USER_NAME']}?")
        
    def on_send(self, event=None):
        user_text = self.user_input.get().strip()
        if user_text:
            self.add_message("You", user_text)
            self.user_input.delete(0, tk.END)
            self.process_command(user_text)
            
    def on_voice(self):
        self.listening = True
        self.status_var.set("Listening...")
        self.play_sound("notification")
        
        def listen_thread():
            command = self.assistant.voice_engine.listen()
            self.listening = False
            self.status_var.set("Ready")
            
            if command:
                self.root.after(0, lambda: self.user_input.insert(0, command))
                self.root.after(0, self.on_send)
                
        threading.Thread(target=listen_thread, daemon=True).start()
        
    def process_command(self, command):
        def process():
            try:
                response = self.assistant.handle_command(command)
                self.root.after(0, lambda: self.add_message("Dazzy", response))
                self.root.after(0, lambda: self.assistant.voice_engine.speak(response))
                
                if any(farewell in command.lower() for farewell in self.assistant.custom_commands["farewells"]):
                    self.root.after(1000, self.root.destroy)
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.root.after(0, lambda: self.add_message("Dazzy", error_msg))
                self.play_sound("error")
                
        threading.Thread(target=process, daemon=True).start()

# 🚀 Main Application
def main():
    root = tk.Tk()
    
    # Set window icon
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
        
    assistant = DazzyAssistant()
    ui = DazzyUI(root, assistant)
    
    def on_closing():
        assistant.voice_engine.speak(f"Goodbye {CONFIG['USER_NAME']}!")
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
