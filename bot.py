import os
import asyncio
import requests
from pymongo import MongoClient
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ChatAction

# ================= ENV =================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

if not all([TOKEN, OPENROUTER_KEY, MONGO_URI, OWNER_ID, SUPPORT_CHANNEL, LOG_CHANNEL_ID]):
    raise RuntimeError("❌ Missing ENV variables")

MODEL = "deepseek/deepseek-chat"

# ================= MongoDB =================
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# ================= Languages =================
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

# ================= OpenRouter =================
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
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ================= /start =================
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

# ================= Buttons =================
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

# ================= Commands =================
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"👤 Your ID: `{update.effective_user.id}`"
    if update.effective_chat.type != "private":
        text += f"\n👥 Group ID: `{update.effective_chat.id}`"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= BAN (reply + username) =================
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    chat = update.effective_chat

    admins = await chat.get_administrators()
    admin_ids = [a.user.id for a in admins]

    target_id = None

    # Case 1: reply
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id

    # Case 2: /ban @username
    elif context.args:
        username = context.args[0].lstrip("@")
        doc = users.find_one({"username": username})
        if doc:
            target_id = doc["user_id"]
        else:
            await update.message.reply_text(
                "❌ User not found.\nUser ne pehle bot/group me message bheja hona chahiye."
            )
            return
    else:
        await update.message.reply_text("Use:\n/ban @username\nor reply + /ban")
        return

    if target_id in admin_ids:
        await update.message.reply_text("❌ Admin ko ban nahi kiya ja sakta.")
        return

    await chat.ban_member(target_id)
    await update.message.reply_text(f"🚫 User banned successfully\nID: {target_id}")

# ================= Image =================
async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Use: /image <prompt>")
        return
    img = f"https://image.pollinations.ai/prompt/{prompt}"
    await update.message.reply_photo(photo=img, caption=prompt)

# ================= Chat =================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    user = update.effective_user

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
        {"$set": {
            "chat_id": chat_id,
            "user_id": user.id,
            "username": user.username,
            "lang": lang,
            "messages": msgs[-20:]
        }},
        upsert=True
    )

    # typing animation
    await update.message.chat.send_action(ChatAction.TYPING)
    await asyncio.sleep(1.5)

    # log
    await context.bot.send_message(
        LOG_CHANNEL_ID,
        f"📝 Chat ID: {chat_id}\n👤 User: @{user.username} ({user.id})\n💬 {text}"
    )

    await update.message.reply_text(reply)

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("language", language))
app.add_handler(CommandHandler("id", get_id))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("image", image))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot running (FINAL VERSION)")
app.run_polling()
