import os
from datetime import datetime

import requests
import wikipedia
from flask import Flask, render_template_string, request, jsonify

# --------------------------------------------------
# 🌱 Environment
# --------------------------------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# --------------------------------------------------
# 🤖 Assistant Logic
# --------------------------------------------------
class DazzyAssistant:
    def handle_command(self, text: str) -> str:
        cmd = text.lower().strip()

        if not cmd:
            return "Say something. Silence doesn’t compute."

        if any(greet in cmd for greet in ("hello", "hi", "hey")):
            return "Hello. Dazzy online. Speak."

        if "time" in cmd:
            return datetime.now().strftime("Time: %I:%M %p")

        if "date" in cmd:
            return datetime.now().strftime("Date: %A, %B %d, %Y")

        if "open youtube" in cmd:
            return (
                "<a href='https://youtube.com' target='_blank' "
                "style='color:#ff4d4d'>Open YouTube</a>"
            )

        if cmd.startswith(("who is", "what is")):
            topic = cmd.replace("who is", "").replace("what is", "").strip()
            if not topic:
                return "Ask properly. Topic missing."

            try:
                return wikipedia.summary(topic, sentences=2, auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError:
                return "That topic is ambiguous. Be specific."
            except wikipedia.exceptions.PageError:
                return "No Wikipedia page found."
            except Exception:
                return "Wikipedia lookup failed."

        return self.ask_deepseek(text)

    def ask_deepseek(self, prompt: str) -> str:
        if not DEEPSEEK_API_KEY:
            return "Offline mode. DeepSeek API key not configured."

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            return "DeepSeek connection failed."

# --------------------------------------------------
# 🌐 Flask App
# --------------------------------------------------
app = Flask(__name__)
assistant = DazzyAssistant()

# --------------------------------------------------
# 🎨 GUI (HTML + CSS + JS)
# --------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dazzy AI</title>
    <style>
        body {
            background: #0a0101;
            color: #f1faee;
            font-family: Arial;
            margin: 0;
            display: flex;
            height: 100vh;
        }
        #chat {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        .user { color: #ff4d6d; text-align: right; margin: 10px; }
        .bot { color: #f1faee; text-align: left; margin: 10px; }
        #input {
            position: fixed;
            bottom: 0;
            width: 100%;
            display: flex;
            background: #140303;
        }
        input {
            flex: 1;
            padding: 15px;
            background: #250808;
            border: none;
            color: white;
            font-size: 16px;
        }
        button {
            padding: 15px 30px;
            background: #e63946;
            border: none;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>
<body>

<div id="chat">
    <div class="bot">Dazzy online. Awaiting command.</div>
</div>

<div id="input">
    <input id="msg" placeholder="Type here..." autofocus />
    <button onclick="send()">SEND</button>
</div>

<script>
async function send() {
    const input = document.getElementById("msg");
    const text = input.value.trim();
    if (!text) return;

    const chat = document.getElementById("chat");
    chat.innerHTML += `<div class="user">${text}</div>`;
    input.value = "";

    const res = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: text})
    });

    const data = await res.json();
    chat.innerHTML += `<div class="bot">${data.reply}</div>`;
    chat.scrollTop = chat.scrollHeight;
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    reply = assistant.handle_command(data.get("message", ""))
    return jsonify({"reply": reply})

# --------------------------------------------------
# 🚀 Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
