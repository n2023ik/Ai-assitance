import os
import json
import random
import logging
from datetime import datetime

import requests
import wikipedia
from flask import Flask, render_template_string, request, jsonify

# --------------------------------------------------
# 🌱 Environment & Config
# --------------------------------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# --------------------------------------------------
# 🤖 Assistant Logic
# --------------------------------------------------
class DazzyAssistant:
    def __init__(self):
        self.user_name = "User"

    def handle_command(self, text):
        cmd = text.lower().strip()
        
        # Logic Map
        if any(greet in cmd for greet in ["hello", "hi", "hey"]):
            return f"Hello! I'm Dazzy. Ready to ignite some ideas today?"
        elif "time" in cmd:
            return datetime.now().strftime("The clock strikes %I:%M %p.")
        elif "date" in cmd:
            return datetime.now().strftime("It is currently %A, %B %d, %Y.")
        elif "open youtube" in cmd:
            return "On a desktop, I'd open the browser. Here, you can click: <a href='https://youtube.com' target='_blank' style='color:#ff4d4d'>Open YouTube</a>"
        elif "who is" in cmd or "what is" in cmd:
            try:
                topic = cmd.replace("who is", "").replace("what is", "").strip()
                return wikipedia.summary(topic, sentences=2)
            except:
                return "My crimson sensors couldn't find a Wikipedia entry for that. Want to try a different topic?"
        
        # Fallback to DeepSeek
        return self.ask_deepseek(text)

    def ask_deepseek(self, prompt):
        if not DEEPSEEK_API_KEY:
            return "Offline Mode: DeepSeek API key is missing in server environment variables."
        
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
            return f"Thermal Overload: Encountered a connection issue with DeepSeek."

# --------------------------------------------------
# 🌐 Web Server (Flask)
# --------------------------------------------------
app = Flask(__name__)
assistant = DazzyAssistant()

# Embedded Red Design Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dazzy AI | Red Edition</title>
    <style>
        :root {
            --bg-main: #0a0101;
            --bg-sidebar: #1a0505;
            --bg-chat: #140303;
            --accent-red: #e63946;
            --text-main: #f1faee;
            --text-dim: #a8a8a8;
            --user-red: #ff4d6d;
        }

        body, html {
            margin: 0; padding: 0; height: 100%;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            display: flex;
        }

        /* Sidebar */
        #sidebar {
            width: 260px;
            background-color: var(--bg-sidebar);
            display: flex;
            flex-direction: column;
            align-items: center;
            border-right: 1px solid #300;
        }

        .logo { font-size: 40px; margin-top: 40px; color: var(--accent-red); }
        .title { font-weight: bold; letter-spacing: 2px; margin-top: 10px; }
        .status { font-size: 10px; margin-top: 20px; color: var(--text-dim); display: flex; align-items: center; }
        .dot { height: 8px; width: 8px; background: #43b581; border-radius: 50%; margin-right: 8px; }

        /* Main Chat */
        #main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 30px;
            max-width: 1000px;
            margin: 0 auto;
        }

        #chat-display {
            flex: 1;
            background-color: var(--bg-chat);
            border-radius: 12px;
            padding: 20px;
            overflow-y: auto;
            border: 1px solid #220;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .message { max-width: 85%; line-height: 1.5; }
        .user-msg { align-self: flex-end; color: var(--user-red); text-align: right; }
        .ai-msg { align-self: flex-start; color: var(--text-main); }
        .msg-header { font-size: 10px; font-weight: bold; margin-bottom: 4px; text-transform: uppercase; opacity: 0.6; }

        /* Input Area */
        #input-area {
            margin-top: 20px;
            display: flex;
            gap: 15px;
        }

        input {
            flex: 1;
            background: #250808;
            border: 1px solid #411;
            border-radius: 8px;
            padding: 15px;
            color: white;
            outline: none;
            font-size: 16px;
        }

        input:focus { border-color: var(--accent-red); }

        button {
            background: var(--accent-red);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0 30px;
            cursor: pointer;
            font-weight: bold;
            transition: 0.3s;
        }

        button:hover { background: #ff4d4d; transform: scale(1.05); }
        button:disabled { background: #444; cursor: not-allowed; }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #300; border-radius: 10px; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="logo">✦</div>
        <div class="title">DAZZY AI</div>
        <div class="status"><div class="dot"></div> ONLINE (RED OPS)</div>
    </div>
    <div id="main">
        <div id="chat-display">
            <div class="message ai-msg">
                <div class="msg-header">System</div>
                Neural link established. Crimson protocols active. How can I assist?
            </div>
        </div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="Enter command..." autofocus>
            <button id="send-btn">SEND</button>
        </div>
    </div>

    <script>
        const chatDisplay = document.getElementById('chat-display');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        function appendMessage(sender, text, isAi) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isAi ? 'ai-msg' : 'user-msg'}`;
            msgDiv.innerHTML = `<div class="msg-header">${sender}</div><div>${text}</div>`;
            chatDisplay.appendChild(msgDiv);
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            userInput.value = '';
            appendMessage('You', text, false);

            sendBtn.disabled = true;
            sendBtn.innerText = '...';

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                appendMessage('Dazzy', data.reply, true);
            } catch (err) {
                appendMessage('System', 'Connection error.', true);
            } finally {
                sendBtn.disabled = false;
                sendBtn.innerText = 'SEND';
            }
        }

        sendBtn.onclick = sendMessage;
        userInput.onkeypress = (e) => { if(e.key === 'Enter') sendMessage(); };
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_message = data.get("message", "")
    reply = assistant.handle_command(user_message)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    # Use port 10000 for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
