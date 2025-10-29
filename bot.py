import os
import sqlite3
from flask import Flask, jsonify, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "6065570955:AAHIUsfGhc2MmQ3EiJtOw5ozzyQ7EzmWsmA")

# ---------- DATABASE ---------- #
def init_db():
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def save_token(token: str):
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tokens (token) VALUES (?)", (token,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_tokens():
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM tokens")
    tokens = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tokens


# ---------- TELEGRAM ---------- #
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


# ---------- FLASK ---------- #
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "Bot and server are running!"})


# ---------- MAIN ---------- #
async def main():
    init_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("tokens", tokens_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("✅ Telegram bot started successfully.")

    # Instead of using threads, run Flask and bot together on same event loop
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{os.environ.get('PORT', 10000)}"]

    # Run Flask + Bot concurrently
    import asyncio
    await asyncio.gather(
        serve(app, config),
        application.run_polling()
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
