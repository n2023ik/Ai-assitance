import os
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# --------------------------------------------------
# 📚 Load Dataset
# --------------------------------------------------
with open("data.json", "r", encoding="utf-8") as f:
    DATASET = json.load(f)

# --------------------------------------------------
# 🤖 Assistant Logic (Dataset Based)
# --------------------------------------------------
class DazzyAssistant:
    def handle_command(self, text: str) -> str:
        cmd = text.lower().strip()

        if not cmd:
            return "Say something. Silence doesn’t compute."

        # Direct dataset lookup
        if cmd in DATASET:
            value = DATASET[cmd]

            if value == "TIME_COMMAND":
                return datetime.now().strftime("Time: %I:%M %p")

            if value == "DATE_COMMAND":
                return datetime.now().strftime("Date: %A, %B %d, %Y")

            return value

        # Fallback
        return "I don’t have this in my knowledge base yet."

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
    <div class="bot">Dazzy online. Knowledge base loaded.</div>
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
