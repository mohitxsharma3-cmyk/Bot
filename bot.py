import os
import sqlite3
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

# Get Telegram bot token from environment or fallback
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ---------- DATABASE SETUP ---------- #
def init_db():
    if not os.path.exists("tokens.db"):
        conn = sqlite3.connect("tokens.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE
            )
            """
        )
        conn.commit()
        conn.close()


def save_token(token: str):
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tokens (token) VALUES (?)", (token,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Token already exists
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


# ---------- TELEGRAM COMMANDS ---------- #
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


# ---------- FLASK APP FOR
