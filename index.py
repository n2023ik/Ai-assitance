import os
import json
import re
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session
import wikipedia

# --------------------------------------------------
# ⚙️ Flask setup
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = "dazzy-secret-key"

# --------------------------------------------------
# 📚 Load Dataset
# --------------------------------------------------
with open("data.json", "r", encoding="utf-8") as f:
    DATASET = json.load(f)

# --------------------------------------------------
# 🤖 Assistant Logic
# --------------------------------------------------
class DazzyAssistant:
    def handle(self, text: str) -> str:
        cmd = text.lower().strip()

        if not cmd:
            return "Say something."

        # Time / Date
        if cmd in DATASET:
            action = DATASET[cmd]

            if action == "TIME_COMMAND":
                return datetime.now().strftime("Time: %I:%M %p")

            if action == "DATE_COMMAND":
                return datetime.now().strftime("Date: %A, %B %d, %Y")

            if action == "OPEN_YOUTUBE":
                return "<a href='https://youtube.com' target='_blank'>Open YouTube</a>"

            if action == "OPEN_GOOGLE":
                return "<a href='https://google.com' target='_blank'>Open Google</a>"

            if action == "OPEN_GMAIL":
                return "<a href='https://mail.google.com' target='_blank'>Open Gmail</a>"
                
                if action == "geeksforgeeks":
                return "<a href='https://www.geeksforgeeks.org/' target='_blank'>geeksforgeeks</a>"

             if action == "instagram":
                return "<a href='https://www.instagram.com/' target='_blank'>instagram</a>"

            return action

        # Calculator
        if cmd.startswith(("calculate", "math")):
            return self.calculate(cmd)

        # Wikipedia
        if cmd.startswith(("who is", "what is")):
            return self.wiki(cmd)

        return "I don’t know that yet."

    def calculate(self, text):
        expr = re.sub(r"[^0-9+\-*/(). ]", "", text)
        try:
            return f"Result: {eval(expr)}"
        except:
            return "Invalid calculation."

    def wiki(self, text):
        topic = (
            text.replace("who is", "")
            .replace("what is", "")
            .strip()
        )
        if not topic:
            return "Specify a topic."

        try:
            return wikipedia.summary(topic, sentences=2, auto_suggest=False)
        except wikipedia.exceptions.DisambiguationError:
            return "Topic is ambiguous."
        except wikipedia.exceptions.PageError:
            return "No Wikipedia page found."
        except:
            return "Wikipedia error."

assistant = DazzyAssistant()

# --------------------------------------------------
# 🎨 UI
# --------------------------------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Dazzy AI</title>
<style>
body {
    margin:0;
    font-family:Arial;
    background:#0a0101;
    color:#f1faee;
}
#container {
    height:100vh;
    display:flex;
    flex-direction:column;
}
#chat {
    flex:1;
    padding:20px;
    overflow-y:auto;
}
.user { text-align:right; color:#ff4d6d; margin:8px; }
.bot { text-align:left; margin:8px; }
#input {
    display:flex;
    background:#140303;
}
input {
    flex:1;
    padding:15px;
    background:#250808;
    border:none;
    color:white;
    font-size:16px;
}
button {
    padding:15px 25px;
    background:#e63946;
    border:none;
    color:white;
    font-weight:bold;
    cursor:pointer;
}
</style>
</head>
<body>

<div id="container">
    <div id="chat"></div>
    <div id="input">
        <input id="msg" placeholder="Type here..." />
        <button onclick="send()">SEND</button>
    </div>
</div>

<script>
let stage = "name";

const chat = document.getElementById("chat");

function bot(text){
    chat.innerHTML += `<div class="bot">${text}</div>`;
    chat.scrollTop = chat.scrollHeight;
}

function user(text){
    chat.innerHTML += `<div class="user">${text}</div>`;
}

bot("Hello 👋 What is your name?");

async function send(){
    const input = document.getElementById("msg");
    const text = input.value.trim();
    if(!text) return;

    user(text);
    input.value = "";

    const res = await fetch("/ask", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ message:text })
    });

    const data = await res.json();
    bot(data.reply);
}
</script>

</body>
</html>
"""

# --------------------------------------------------
# 🌐 Routes
# --------------------------------------------------
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ask", methods=["POST"])
def ask():
    msg = request.json.get("message","")

    if "name" not in session:
        session["name"] = msg
        return jsonify({
            "reply": f"Nice to meet you, {msg}! What do you want to do today?"
        })

    reply = assistant.handle(msg)
    return jsonify({"reply": reply})

# --------------------------------------------------
# 🚀 Run
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
