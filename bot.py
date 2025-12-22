import os
import requests
from pymongo import MongoClient
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ===== ENV =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
OWNER_USERNAME = os.getenv("OWNER_USERNAME")
START_IMAGE = os.getenv("START_IMAGE_URL")

if not all([TOKEN, OPENROUTER_KEY, MONGO_URI]):
    raise RuntimeError("❌ Missing ENV variables")

MODEL = "deepseek/deepseek-chat"

# ===== MongoDB =====
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
collection = db["chat_history"]

# ===== OpenRouter =====
def ask_ai(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"model": MODEL, "messages": messages}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    return r.json()["choices"][0]["message"]["content"]

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👑 Owner", callback_data="owner")],
        [InlineKeyboardButton("🔫 Shoot (Reset Chat)", callback_data="shoot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=START_IMAGE,
        caption="🤖 AI Bot Online\nMemory enabled.\nUse buttons below 👇",
        reply_markup=reply_markup
    )

# ===== Buttons =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id

    if query.data == "owner":
        await query.message.reply_text(
            f"👑 Owner: @{OWNER_USERNAME}\n📩 Contact for support"
        )

    elif query.data == "shoot":
        collection.delete_one({"chat_id": chat_id})
        await query.message.reply_text("🔫 Chat memory cleared successfully.")

# ===== Chat =====
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    doc = collection.find_one({"chat_id": chat_id})
    messages = doc["messages"] if doc else []

    messages.append({"role": "user", "content": text})
    reply = ask_ai(messages)
    messages.append({"role": "assistant", "content": reply})

    collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"messages": messages[-20:]}},
        upsert=True
    )

    await update.message.reply_text(reply)

# ===== Run =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot running with buttons + image + memory")
app.run_polling()
