import os
import sqlite3
from threading import Thread
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize SQLite database
def init_db():
    if not os.path.exists('tokens.db'):
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE
        )''')
        conn.commit()
        conn.close()

def save_token(token: str):
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO tokens (token) VALUES (?)', (token,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Token already exists
        pass
    finally:
        conn.close()

def get_tokens():
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT token FROM tokens')
    tokens = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tokens

# Telegram bot command handlers
def tokens_command(update: Update, context: CallbackContext):
    tokens = get_tokens()
    if tokens:
        update.message.reply_text("
".join(tokens))
    else:
        update.message.reply_text("No tokens stored yet.")

def message_handler(update: Update, context: CallbackContext):
    token = update.message.text.strip()
    save_token(token)
    update.message.reply_text("Token received and saved.")

# Flask app for uptime and health check
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "Bot server is running"})

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def run_telegram_bot():
    init_db()
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("tokens", tokens_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # Start Flask app in a separate thread
    Thread(target=run_flask).start()
    # Start Telegram bot in main thread
    run_telegram_bot()