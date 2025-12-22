import os
import requests
import random
from pymongo import MongoClient
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================= ENV =================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not all([TOKEN, OPENROUTER_KEY, MONGO_URI, OWNER_ID]):
    raise RuntimeError("Missing ENV variables")

MODEL = "deepseek/deepseek-chat"

# ================= MongoDB =================
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]
blocked = db["blocked_users"]

# ================= Helpers =================
def is_owner(uid): return uid == OWNER_ID
def is_blocked(uid): return blocked.find_one({"user_id": uid, "blocked": True})

async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return False
    member = await context.bot.get_chat_member(chat.id, user.id)
    return member.status in ["administrator", "creator"]

# ================= Language =================
LANG_PROMPTS = {
    "en": "Reply only in English.",
    "hi": "केवल हिंदी में उत्तर दें।"
}

LANG_BUTTONS = [
    [("🇮🇳 Hindi", "lang_hi"), ("🇬🇧 English", "lang_en")]
]

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

# ================= BOT =================
app = ApplicationBuilder().token(TOKEN).build()

# ---------- /language ----------
async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(t, callback_data=d) for t, d in row] for row in LANG_BUTTONS]
    await update.message.reply_text(
        "🌍 Choose language",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def language_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_")[1]
    users.update_one(
        {"chat_id": q.message.chat_id},
        {"$set": {"lang": lang}},
        upsert=True
    )
    await q.message.reply_text(f"✅ Language set to {lang.upper()}")

# ---------- /id ----------
async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f"🆔 Your ID: `{u.id}`", parse_mode="Markdown")

# ---------- /joke ----------
async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("😂 Joke soch raha hoon...")

    messages = [
        {"role": "system", "content": "Tell a short, clean, funny joke."},
        {"role": "user", "content": "Tell me a joke"}
    ]

    joke = safe_ai(messages)

    await update.message.reply_text(
        joke,
        reply_to_message_id=update.message.message_id
    )

# ---------- /shayri ----------
async def shayri_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Shayari likh raha hoon...")

    messages = [
        {
            "role": "system",
            "content": "Write a beautiful, short Hindi shayari. Keep it emotional and poetic."
        },
        {"role": "user", "content": "Ek acchi si shayari likho"}
    ]

    shayari = safe_ai(messages)

    await update.message.reply_text(
        shayari,
        reply_to_message_id=update.message.message_id
    )

# ---------- /image ----------
async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text(
            "Use: /image <description>\nExample:\n/image headphones pehni sundar ladki ka DP"
        )
        return

    await update.message.reply_text("🎨 Image generate ho rahi hai, thoda wait karo...")

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "stabilityai/sdxl",
                "prompt": prompt,
                "size": "1024x1024"
            },
            timeout=120
        )
        r.raise_for_status()
        img_url = r.json()["data"][0]["url"]

        await update.message.reply_photo(
            photo=img_url,
            caption=f"🖼 Generated Image\n\nPrompt:\n{prompt}"
        )

    except Exception as e:
        await update.message.reply_text(
            "❌ Image generate nahi ho paayi.\nBaad me try karo."
        )

# ---------- GROUP BAN ----------
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    chat = update.effective_chat
    target = None

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target = int(context.args[0])
        except:
            await update.message.reply_text("Invalid user ID")
            return

    if not target:
        await update.message.reply_text("Reply or use /ban <user_id>")
        return

    await context.bot.ban_chat_member(chat.id, target)
    await update.message.reply_text("🚫 User banned")

# ---------- CHAT ----------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blocked(user.id):
        return

    chat_id = update.effective_chat.id
    doc = users.find_one({"chat_id": chat_id}) or {}
    msgs = doc.get("messages", [])
    lang = doc.get("lang", "en")

    if not msgs:
        msgs.append({
            "role": "system",
            "content": LANG_PROMPTS.get(lang, LANG_PROMPTS["en"])
        })

    msgs.append({"role": "user", "content": update.message.text})
    reply = ask_ai(msgs)
    msgs.append({"role": "assistant", "content": reply})

    users.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "chat_id": chat_id,
            "user_id": user.id,
            "username": user.username,
            "messages": msgs[-20:]
        }},
        upsert=True
    )

    mention = f"[{user.first_name}](tg://user?id={user.id})"
    await update.message.reply_text(
        f"{mention}\n{reply}",
        parse_mode="Markdown",
        reply_to_message_id=update.message.message_id
    )

# ---------- OWNER DASHBOARD ----------
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(
        f"📊 DASHBOARD\n"
        f"👤 Users: {users.count_documents({})}\n"
        f"🚫 Blocked: {blocked.count_documents({'blocked': True})}"
    )

# ================= HANDLERS =================
app.add_handler(CommandHandler("language", language_cmd))
app.add_handler(CallbackQueryHandler(language_buttons))
app.add_handler(CommandHandler("id", id_cmd))
app.add_handler(CommandHandler("joke", joke_cmd))
app.add_handler(CommandHandler("shayri", shayri_cmd))
app.add_handler(CommandHandler("image", image_cmd))
app.add_handler(CommandHandler("ban", ban_cmd))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ================= RUN =================
if __name__ == "__main__":
    print("🤖 Bot running in POLLING mode (ALL FEATURES)")
    app.run_polling(drop_pending_updates=True)
