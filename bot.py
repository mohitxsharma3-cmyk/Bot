import os
import sqlite3
import asyncio
from threading import Thread
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ====== BOT TOKEN ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "6065570955:AAHIUsfGhc2MmQ3EiJtOw5ozzyQ7EzmWsmA")

# ====== DATABASE SETUP ======
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
        # Ignore duplicates
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

# ====== TELEGRAM COMMANDS ======
async def tokens_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tokens = get_tokens()
    if tokens:
        await update.message.reply_text("\n".join(tokens))
    else:
        await update.message.reply_text("No tokens stored yet.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    save_token(token)
    await update.message.reply_text("✅ Token received and saved.")

# ====== FLASK APP (for uptime ping) ======
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "Bot alive and running!"})

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ====== TELEGRAM BOT SETUP ======
async def main():
    init_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command: /tokens
    application.add_handler(CommandHandler("tokens", tokens_command))

    # Save any plain text messages as tokens
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("✅ Telegram bot started successfully.")
    await application.run_polling()

# ====== ENTRY POINT ======
if __name__ == "__main__":
    # Run Flask in a separate thread
    Thread(target=run_flask, daemon=True).start()

    # Render-safe event loop handling
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(main())
            loop.run_forever()
        else:
            loop.run_until_complete(main())
    except RuntimeError:
        asyncio.run(main())
        
