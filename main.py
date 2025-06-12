from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['DATABASE'] = 'database.db'

# OpenRouter API setup with your key
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

# Function to get bot response using Gemma
def get_bot_response(context, question, name):
    instructions = f"""
You are an AI assistant named Buddy 🤖.

Instructions:
- The user's name is {name}.
- Only answer the user's question simply and directly.
- Don't repeat greetings like 'Hey' or 'How can I help you?'
- Do not roleplay or use extra commentary.
- Never say "Buddy:" – just answer.
- Use emojis instead of writing *smiles* or *thinks*.
- If asked about your creator, say you were created by the team members Nandhana, Aravind, Jibin, Ananathakumar.

Conversation history:
{context}

User's Question: {question}

Buddy's Answer:
"""
    completion = client.chat.completions.create(
        model="google/gemma-3n-e4b-it:free",
        extra_headers={
            "HTTP-Referer": "http://localhost:5000",  # optional
            "X-Title": "ResumeAI Chatbot"
        },
        messages=[
            {"role": "user", "content": instructions.strip()}
        ]
    )
    return completion.choices[0].message.content.strip()

# Initialize the SQLite database
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', username=session['username'])

@app.route('/start-chat', methods=['POST'])
def start_chat():
    username = request.form.get('username')
    if not username:
        return jsonify({'status': 'error', 'message': 'Username is required'})
    
    try:
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = cursor.fetchone()[0]
            conn.commit()

        session['username'] = username
        session['user_id'] = user_id

        response = get_bot_response("", f"My name is {username}", username)

        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)",
                (user_id, f"My name is {username}", response)
            )
            conn.commit()

        return jsonify({'status': 'success', 'username': username, 'response': response})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/send-message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Session expired'})

    message = request.json.get('message')
    if not message:
        return jsonify({'status': 'error', 'message': 'No message provided'})
    
    try:
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message, response FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5",
                (session['user_id'],)
            )
            history = cursor.fetchall()

        context = "\n".join([f"User: {m}\nBuddy: {r}" for m, r in reversed(history)])

        response = get_bot_response(context, message, session['username'])

        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)",
                (session['user_id'], message, response)
            )
            conn.commit()

        return jsonify({
            'status': 'success',
            'response': response,
            'timestamp': datetime.now().strftime("%H:%M")
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get-history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Session expired'})

    try:
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message, response, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp ASC",
                (session['user_id'],)
            )
            history = cursor.fetchall()

        formatted_history = []
        for msg, res, timestamp in history:
            formatted_history.append({'type': 'user', 'message': msg, 'timestamp': timestamp})
            formatted_history.append({'type': 'bot', 'message': res, 'timestamp': timestamp})

        return jsonify({'status': 'success', 'history': formatted_history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
