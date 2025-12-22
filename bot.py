import os
import requests
from pymongo import MongoClient
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ========= ENV =========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

if not all([TOKEN, OPENROUTER_KEY, MONGO_URI, OWNER_ID, SUPPORT_CHANNEL, LOG_CHANNEL_ID]):
    raise RuntimeError("Missing ENV variables")

MODEL = "deepseek/deepseek-chat"

# ========= MongoDB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# ========= Languages =========
LANG = {
    "en": "Reply only in English.",
    "hi": "केवल हिंदी में उत्तर दें।",
    "es": "Responde solo en español.",
    "fr": "Répondez uniquement en français."
}

LANG_BTN = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 Hindi",
    "es": "🇪🇸 Spanish",
    "fr": "🇫🇷 French"
}

# ========= OpenRouter =========
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

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🌍 Language", callback_data="language")],
        [InlineKeyboardButton("📢 Support Channel", url=SUPPORT_CHANNEL)]
    ]
    await update.message.reply_photo(
        photo="https://i.imgur.com/4M34hi2.jpg",
        caption="🤖 AI Bot Online\nChoose options below 👇",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ========= BUTTONS =========
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "language":
        btns = [[InlineKeyboardButton(v, callback_data=f"lang_{k}")]
                for k, v in LANG_BTN.items()]
        await q.message.reply_text(
            "🌍 Select Language:",
            reply_markup=InlineKeyboardMarkup(btns)
        )

    elif q.data.startswith("lang_"):
        code = q.data.split("_")[1]
        users.update_one(
            {"chat_id": q.message.chat_id},
            {"$set": {"lang": code, "messages": []}},
            upsert=True
        )
        await q.message.reply_text(f"✅ Language set to {LANG_BTN[code]}")

# ========= COMMANDS =========
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"👤 Your ID: `{update.effective_user.id}`"
    if update.effective_chat.type != "private":
        text += f"\n👥 Group ID: `{update.effective_chat.id}`"
    await update.message.reply_text(text, parse_mode="Markdown")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user to ban.")
        return
    await update.effective_chat.ban_member(
        update.message.reply_to_message.from_user.id
    )
    await update.message.reply_text("🚫 User banned.")

async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Use: /image <prompt>")
        return
    img = f"https://image.pollinations.ai/prompt/{prompt}"
    await update.message.reply_photo(photo=img, caption=prompt)

# ========= CHAT =========
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    doc = users.find_one({"chat_id": chat_id}) or {}
    lang = doc.get("lang", "en")
    msgs = doc.get("messages", [])

    if not msgs:
        msgs.append({"role": "system", "content": LANG[lang]})

    msgs.append({"role": "user", "content": text})
    reply = ask_ai(msgs)
    msgs.append({"role": "assistant", "content": reply})

    users.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, "lang": lang, "messages": msgs[-20:]}},
        upsert=True
    )

    # LOG
    await context.bot.send_message(
        LOG_CHANNEL_ID,
        f"📝 Chat ID: {chat_id}\n👤 User: {update.effective_user.id}\n💬 {text}"
    )

    await update.message.reply_text(reply)

# ========= RUN =========
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("language", language))
app.add_handler(CommandHandler("id", get_id))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("image", image))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot running with FULL features")
app.run_polling()
