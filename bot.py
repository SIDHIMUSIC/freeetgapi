import os
import requests
import random
import asyncio
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
def is_owner(uid): 
    return uid == OWNER_ID

def is_blocked(uid): 
    return blocked.find_one({"user_id": uid, "blocked": True}) is not None

async def is_admin(update, context):
    chat = update.effective_chat
    if chat.type == "private":
        return False
    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    return member.status in ("administrator", "creator")

# ================= Language =================
LANG_PROMPTS = {
    "en": (
        "Reply only in English. "
        "Write like a human, soft handwritten style. "
        "Use emojis ONLY when they naturally fit the emotion."
    ),
    "hi": (
        "केवल हिंदी में उत्तर दें। "
        "इंसान की तरह नरम लिखावट रखें। "
        "जहाँ भावनात्मक रूप से सही लगे वहीं इमोजी का प्रयोग करें।"
    )
}

LANG_BUTTONS = [
    [("🇮🇳 Hindi", "lang_hi"), ("🇬🇧 English", "lang_en")]
]

# ================= SAFE AI =================
def safe_ai(messages):
    try:
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
    except Exception:
        return "🙂 अभी थोड़ी दिक्कत आ रही है, थोड़ी देर बाद फिर कोशिश करें।"

# ================= TYPEWRITER EFFECT =================
async def typewriter_reply(update, context, text, delay=0.6):
    chat_id = update.effective_chat.id
    text = text.strip()
    parts = []

    while len(text) > 0:
        if len(text) > 80:
            cut = text[:80].rfind(" ")
            cut = cut if cut != -1 else 80
        else:
            cut = len(text)
        parts.append(text[:cut])
        text = text[cut:].lstrip()

    for part in parts:
        await context.bot.send_chat_action(chat_id, "typing")
        await asyncio.sleep(delay)
        await update.message.reply_text(part)

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
    users.update_one({"chat_id": q.message.chat_id}, {"$set": {"lang": lang}}, upsert=True)
    await q.message.reply_text(f"✅ Language set to {lang.upper()}")

# ---------- /id ----------
async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 Your ID: `{update.effective_user.id}`",
        parse_mode="Markdown"
    )

# ---------- /joke ----------
async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = [
        {"role": "system", "content": "Tell a short, clean, funny joke. Use emoji only if it fits."},
        {"role": "user", "content": "Tell me a joke"}
    ]
    reply = safe_ai(messages)
    await typewriter_reply(update, context, reply)

# ---------- /shayri ----------
async def shayri_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = [
        {
            "role": "system",
            "content": (
                "Write a beautiful short Hindi shayari. "
                "Emotional, poetic. Use emoji only if it fits naturally."
            )
        },
        {"role": "user", "content": "Ek acchi si shayari likho"}
    ]
    reply = safe_ai(messages)
    await typewriter_reply(update, context, reply)

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
    except Exception:
        await update.message.reply_text("❌ Image generate nahi ho paayi.")

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
            return

    if target:
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
    reply = safe_ai(msgs)
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
    await typewriter_reply(update, context, f"{mention}\n{reply}")

# ---------- OWNER PANEL ----------
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
    print("🤖 Bot running in POLLING mode (FINAL HUMAN STYLE)")
    app.run_polling(drop_pending_updates=True)
