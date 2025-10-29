import os
import sqlite3
from threading import Thread
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace this with your actual Telegram bot token or set BOT_TOKEN as an environment variable in Render
BOT_TOKEN = os.getenv("BOT_TOKEN", "6065570955:AAHIUsfGhc2MmQ3EiJtOw5ozzyQ7EzmWsmA")


# ---------- DATABASE SETUP ---------- #
def init_db():
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE
        )
    ''')
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


# ---------- TELEGRAM HANDLERS ---------- #
def tokens_command(update: Update, context: CallbackContext):
    tokens = get_tokens()
    if tokens:
        update.message.reply_text("\n".join(tokens))  # ✅ fixed syntax error
    else:
        update.message.reply_text("No tokens stored yet.")


def message_handler(update: Update, context: CallbackContext):
    token = update.message.text.strip()
    save_token(token)
    update.message.reply_text("✅ Token received and saved.")


# ---------- FLASK SERVER ---------- #
app = Flask(__name__)


@app.route('/')
def home():
    return jsonify({"status": "Bot alive!"})


def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


# ---------- TELEGRAM BOT ---------- #
def run_bot():
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)  # safer with use_context
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("tokens", tokens_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    print("✅ Telegram bot is running...")
    updater.start_polling()
    updater.idle()


# ---------- MAIN ENTRY ---------- #
if __name__ == "__main__":
    # Start Flask web server in a background thread
    Thread(target=run_flask, daemon=True).start()
    # Start Telegram bot in main thread
    run_bot()
    
