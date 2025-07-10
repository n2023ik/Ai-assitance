import speech_recognition as sr
import pyttsx3
import webbrowser
import wikipedia
import requests
from googletrans import Translator

# 🔑 DeepSeek API Key
DEEPSEEK_API_KEY = "sk-12ac850b37194f0ca495f958dd230407"

# 🎤 Initialize engines
engine = pyttsx3.init()
recognizer = sr.Recognizer()
translator = Translator()

# 🗣️ Text-to-Speech
def speak(text):
    print("Dazzy says:", text)
    engine.say(text)
    engine.runAndWait()

# 🎧 Voice Recognition
def listen():
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"👂 You said: {text}")
        return text.lower()
    except Exception as e:
        print("❌ Could not understand:", e)
        return ""

# 🤖 Ask DeepSeek
def ask_dazzy(prompt):
    if not DEEPSEEK_API_KEY:
        return "DeepSeek API key is not set. Cannot fetch a response."

    url = "https://api.deepseek.com/v1/chat/completions"  # Correct endpoint
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",  # Use this for free tier as per DeepSeek's docs
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
            print("DeepSeek API HTTP error: Payment Required (quota exceeded or paid model).")
            return "Your DeepSeek free quota is exhausted or this model requires payment."
        print("DeepSeek API HTTP error:", e)
        return "There was an issue communicating with DeepSeek."
    except requests.exceptions.RequestException as e:
        print("DeepSeek API Error:", e)
        return "Sorry, DeepSeek is unavailable."

# 🧠 Command Handler
def handle_command(command):
    cmd = command.lower()
    if "open youtube" in cmd:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube.")
    elif "search" in cmd or "google" in cmd:
        # Extract query after 'search' or 'google'
        if "search" in cmd:
            query = cmd.split("search",1)[1].strip()
        else:
            query = cmd.split("google",1)[1].strip()
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        speak(f"Searching for {query}")
    elif (
        "wikipedia" in cmd
        or cmd.startswith("who is")
        or cmd.startswith("what is")
        or cmd.startswith("tell me about")
    ):
        # Extract topic
        topic = cmd
        for prefix in ["wikipedia", "who is", "what is", "tell me about"]:
            if topic.startswith(prefix):
                topic = topic.replace(prefix, "", 1).strip()
        try:
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
        except Exception:
            speak("Sorry, I couldn't find that on Wikipedia.")
    elif cmd in ["exit", "stop", "bye"]:
        speak("Goodbye from Dazzy!")
        exit(0)
    else:
        response = ask_dazzy(command)
        if "quota is exhausted" in response or "requires payment" in response:
            # Try Wikipedia as fallback
            try:
                summary = wikipedia.summary(command, sentences=2)
                speak(summary)
            except Exception:
                speak("Sorry, I couldn't find that on Wikipedia or DeepSeek.")
        else:
            speak(response)

# 🚀 Main Loop
if __name__ == "__main__":
    speak("Hello, I'm Dazzy! Your voice assistant is ready.")
    try:
        while True:
            text = listen()
            if text:
                translated = translator.translate(text, dest='en')
                handle_command(translated.text)
    except KeyboardInterrupt:
        speak("Goodbye from Dazzy!")