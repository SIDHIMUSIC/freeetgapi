import os
import threading
import requests
from flask import Flask, jsonify
from pymongo import MongoClient
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# ========== ENV ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not all([TOKEN, OPENROUTER_KEY, MONGO_URI, OWNER_ID]):
    raise RuntimeError("Missing ENV variables")

MODEL = "deepseek/deepseek-chat"

# ========== Mongo ==========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_col = db["users"]

# ========== Language ==========
LANG_MAP = {
    "en": "Reply only in English.",
    "hi": "केवल हिंदी में उत्तर दें।",
    "zh": "请只用中文回答。",
    "es": "Responde solo en español."
}

# ========== OpenRouter ==========
def ask_ai(messages):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        },
        json={"model": MODEL, "messages": messages},
        timeout=60
    )
    return r.json()["choices"][0]["message"]["content"]

# ========== Chat ==========
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    chat_id = msg.chat_id
    text = msg.text

    # Group logic: only reply if mentioned or /ai
    if msg.chat.type in ["group", "supergroup"]:
        if not ("/ai" in text.lower() or context.bot.username in text):
            return
        text = text.replace("/ai", "").strip()

    doc = users_col.find_one({"chat_id": chat_id}) or {}
    lang = doc.get("lang", "en")
    history = doc.get("messages", [])

    if not history:
        history.append({"role": "system", "content": LANG_MAP[lang]})

    history.append({"role": "user", "content": text})
    reply = ask_ai(history)
    history.append({"role": "assistant", "content": reply})

    users_col.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "chat_id": chat_id,
            "lang": lang,
            "messages": history[-20:],
            "type": msg.chat.type
        }},
        upsert=True
    )

    await msg.reply_text(reply)

# ========== Admin ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    total = users_col.count_documents({})
    groups = users_col.count_documents({"type": {"$ne": "private"}})
    await update.message.reply_text(
        f"📊 Stats\nUsers: {total}\nGroups: {groups}"
    )

async def reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    users_col.update_many({}, {"$set": {"messages": []}})
    await update.message.reply_text("♻️ All memory cleared")

# ========== Dashboard ==========
app_web = Flask(__name__)

@app_web.route("/")
def dashboard():
    return jsonify({
        "users": users_col.count_documents({}),
        "languages": list(LANG_MAP.keys()),
        "status": "running"
    })

def run_dashboard():
    app_web.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# ========== Run ==========
def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("resetall", reset_all))

    threading.Thread(target=run_dashboard).start()
    application.run_polling()

main()
