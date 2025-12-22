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

# ================= ENV =================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "owner")
START_IMAGE = os.getenv("START_IMAGE_URL", "")

if not TOKEN or not OPENROUTER_KEY or not MONGO_URI:
    raise RuntimeError("❌ Missing ENV variables")

MODEL = "deepseek/deepseek-chat"

# ================= MongoDB =================
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
collection = db["chat_history"]

# ================= OpenRouter =================
def ask_ai(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👑 Owner", callback_data="owner")],
        [InlineKeyboardButton("🔫 Shoot (Reset Chat)", callback_data="shoot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "🤖 AI Bot Online\n✅ Memory enabled\n👇 Use buttons below"

    # SAFE: image ho to image, warna text
    if START_IMAGE.startswith("http"):
        try:
            await update.message.reply_photo(
                photo=START_IMAGE,
                caption=text,
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass

    await update.message.reply_text(text, reply_markup=reply_markup)

# ================= Buttons =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "owner":
        await query.message.reply_text(f"👑 Owner: @{OWNER_USERNAME}")

    elif query.data == "shoot":
        collection.delete_one({"chat_id": chat_id})
        await query.message.reply_text("🔫 Chat memory cleared successfully.")

# ================= Chat =================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_text = update.message.text

    doc = collection.find_one({"chat_id": chat_id})
    messages = doc["messages"] if doc and "messages" in doc else []

    messages.append({"role": "user", "content": user_text})

    try:
        reply = ask_ai(messages)
    except Exception:
        await update.message.reply_text("⚠️ AI error, try again.")
        return

    messages.append({"role": "assistant", "content": reply})

    collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"messages": messages[-20:]}},
        upsert=True
    )

    await update.message.reply_text(reply)

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot running (safe mode)")
app.run_polling()
