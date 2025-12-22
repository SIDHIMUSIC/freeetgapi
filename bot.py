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
    "en": "Reply only in English. Write naturally like a human. Use emoji only if it fits.",
    "hi": "केवल हिंदी में उत्तर दें। इंसान की तरह स्वाभाविक लिखें, ज़रूरत हो तभी इमोजी।"
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

# ================= SINGLE TYPING REPLY =================
async def typing_single_reply(update, context, text, delay=0.5):
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id, "typing")
    await asyncio.sleep(delay)
    await update.message.reply_text(
        text,
        reply_to_message_id=update.message.message_id,
        parse_mode="Markdown"
    )

# ================= BOT =================
app = ApplicationBuilder().token(TOKEN).build()

# ---------- /start ----------
START_IMAGES = [
    "https://graph.org/file/705cda02e63f4cb0bdb90-ce4d0ddd3a8cf38b5a.jpg",
    "https://graph.org/file/8c5e8ea95b69e682aed19-22090eb6bb17ce7a54.jpg",
    "https://graph.org/file/556615482003de63f32be-58c192c7e65004f9d4.jpg",
    "https://graph.org/file/bb129887cac5752f0f0f5-70aec0f85376516f16.jpg"
]

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    img = random.choice(START_IMAGES)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Language", callback_data="open_language")],
        [InlineKeyboardButton("ℹ️ Help", url="https://t.me/")],
    ])

    await update.message.reply_photo(
        photo=img,
        caption=(
            f"👋 Hi {update.effective_user.first_name}!\n\n"
            "🤖 Main ek smart AI bot hoon.\n"
            "💬 Mujhse baat karo, joke/shayari lo,\n"
            "🖼️ image banao aur kaafi kuch.\n\n"
            "👇 Shuru karne ke liye niche button dabao"
        ),
        reply_markup=kb
    )

# ---------- /language ----------
async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(t, callback_data=d) for t, d in row] for row in LANG_BUTTONS]
    await update.message.reply_text("🌍 Choose language", reply_markup=InlineKeyboardMarkup(kb))

async def language_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "open_language":
        await language_cmd(update, context)
        return

    lang = q.data.split("_")[1]
    users.update_one({"chat_id": q.message.chat_id}, {"$set": {"lang": lang}}, upsert=True)
    await q.message.reply_text(f"✅ Language set to {lang.upper()}")

# ---------- /id ----------
async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Your ID: `{update.effective_user.id}`", parse_mode="Markdown")

# ---------- /joke ----------
async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = safe_ai([
        {"role": "system", "content": "Tell a short, clean, funny joke. Emoji only if needed."},
        {"role": "user", "content": "Tell me a joke"}
    ])
    await typing_single_reply(update, context, reply)

# ---------- /shayri ----------
async def shayri_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = safe_ai([
        {"role": "system", "content": "Write a short emotional Hindi shayari. Emoji only if it fits."},
        {"role": "user", "content": "Ek shayari likho"}
    ])
    await typing_single_reply(update, context, reply)

# ---------- /image ----------
async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Use: /image <description>")
        return

    await update.message.reply_text("🎨 Image generate ho rahi hai...")

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
        img_url = r.json()["data"][0]["url"]
        await update.message.reply_photo(photo=img_url)
    except:
        await update.message.reply_text("❌ Image generate nahi ho paayi.")

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
        msgs.append({"role": "system", "content": LANG_PROMPTS.get(lang)})

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
    await typing_single_reply(update, context, f"{mention}\n{reply}")

# ================= HANDLERS =================
app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("language", language_cmd))
app.add_handler(CallbackQueryHandler(language_buttons))
app.add_handler(CommandHandler("id", id_cmd))
app.add_handler(CommandHandler("joke", joke_cmd))
app.add_handler(CommandHandler("shayri", shayri_cmd))
app.add_handler(CommandHandler("image", image_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ================= RUN =================
if __name__ == "__main__":
    print("🤖 Bot running in POLLING mode (FINAL CLEAN)")
    app.run_polling(drop_pending_updates=True)
