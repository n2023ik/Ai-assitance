import speech_recognition as sr
import pyttsx3
import webbrowser
import wikipedia
import requests
from googletrans import Translator
import os
import time

# 🔐 DeepSeek API Key
DEEPSEEK_API_KEY = ""<!-- Set your DeepSeek API key here -->"

# 🎙️ Initialize voice engine and recognizer
engine = pyttsx3.init()
recognizer = sr.Recognizer()
translator = Translator()

# 🗣️ Speak Function
def speak(text):
    print(f"\n🎙️ Dazzy says: {text}")
    engine.say(text)
    engine.runAndWait()

# 👂 Listen to user input
def listen():
    with sr.Microphone() as source:
        print("\n🎤 Listening for your command...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"👂 You said: {text}")
        return text.lower()
    except Exception as e:
        print(f"❌ Could not understand audio: {e}")
        speak("I didn't catch that. Please say it again.")
        return ""

# 🤖 Ask DeepSeek AI
def ask_dazzy(prompt):
    if not DEEPSEEK_API_KEY:
        return "API key not set. Cannot fetch response."

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are Dazzy, a smart multilingual voice assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 402:
            return "Your DeepSeek free quota is exhausted or this model requires payment."
        return "There was an issue communicating with DeepSeek."
    except requests.exceptions.RequestException:
        return "Sorry, DeepSeek is unavailable at the moment."

# 🌐 Create and Open HTML
def create_html_file(topic, html_code):
    filename = topic.replace(" ", "_") + ".html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_code)
    speak(f"HTML file '{filename}' has been created and opened.")
    webbrowser.open('file://' + os.path.realpath(filename))

# 🧠 Command Handler
def handle_command(command):
    cmd = command.lower()

    # 🎬 Open YouTube
    if "open youtube" in cmd:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube.")

    # 🔍 YouTube Search
    elif "search youtube for" in cmd or "play on youtube" in cmd:
        query = cmd.split("search youtube for", 1)[1] if "search youtube for" in cmd else cmd.split("play on youtube", 1)[1]
        url = f"https://www.youtube.com/results?search_query={query.strip().replace(' ', '+')}"
        webbrowser.open(url)
        speak(f"Playing {query.strip()} on YouTube.")

    # 🌍 Google Search
    elif "search" in cmd or "google" in cmd:
        query = cmd.split("search", 1)[1] if "search" in cmd else cmd.split("google", 1)[1]
        url = f"https://www.google.com/search?q={query.strip().replace(' ', '+')}"
        webbrowser.open(url)
        speak(f"Showing Google results for {query.strip()}.")

    # 📚 Wikipedia Summary
    elif any(cmd.startswith(prefix) for prefix in ["who is", "what is", "tell me about", "wikipedia"]):
        topic = cmd
        for prefix in ["wikipedia", "who is", "what is", "tell me about"]:
            topic = topic.replace(prefix, "").strip()
        try:
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
        except:
            speak("I couldn't find any information on Wikipedia.")

    # 💻 HTML Generator
    elif any(keyword in cmd for keyword in ["create html", "generate html", "make html", "html page", "html for"]):
        topic = (
            cmd.replace("create html code for", "")
               .replace("generate html for", "")
               .replace("create html", "")
               .replace("make html", "")
               .replace("html page for", "")
               .replace("html for", "")
               .strip()
        )

        if not topic:
            speak("Please specify what kind of HTML page you want me to create.")
            return

        speak(f"Generating HTML page for {topic}...")
        prompt = f"Generate a responsive and simple HTML5 page for '{topic}'. Include title, heading, and relevant input or display elements. Only return the complete HTML code."
        response = ask_dazzy(prompt)

        if "<html" in response.lower():
            create_html_file(topic, response)
        else:
            speak("Sorry, I couldn't generate the HTML code. Your quota might be exhausted or the response was incomplete.")

    # ❌ Exit Command
    elif cmd in ["exit", "stop", "bye", "quit"]:
        speak("Thank you for using Dazzy. Goodbye!")
        exit(0)

    # 🧠 Fallback to DeepSeek or Wikipedia
    else:
        response = ask_dazzy(cmd)
        if "quota is exhausted" in response or "requires payment" in response:
            try:
                summary = wikipedia.summary(cmd, sentences=2)
                speak(summary)
            except:
                speak("No relevant information found.")
        else:
            speak(response)

# 🚀 Main Assistant Loop
if __name__ == "__main__":
    speak("✨ Hello! I'm Dazzy, your AI-powered voice assistant. How can I help you today?")
    try:
        while True:
            user_input = listen()
            if user_input:
                translated = translator.translate(user_input, dest='en')
                handle_command(translated.text)
            time.sleep(1)
    except KeyboardInterrupt:
        speak("Session ended. Goodbye!")
