import os
import requests
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

# ================= Languages (MANUAL) =================
LANG_PROMPTS = {
    "en": "Reply only in English.",
    "hi": "केवल हिंदी में उत्तर दें।",
    "es": "Responde solo en español.",
    "fr": "Répondez uniquement en français.",
    "de": "Antworten Sie nur auf Deutsch.",
    "zh": "请只用中文回答。"
}

LANG_BUTTONS = [
    [("🇮🇳 Hindi", "lang_hi"), ("🇬🇧 English", "lang_en")],
    [("🇪🇸 Spanish", "lang_es"), ("🇫🇷 French", "lang_fr")],
    [("🇩🇪 German", "lang_de"), ("🇨🇳 Chinese", "lang_zh")]
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
    keyboard = [
        [InlineKeyboardButton(text, callback_data=data) for text, data in row]
        for row in LANG_BUTTONS
    ]
    await update.message.reply_text(
        "🌍 *Choose your language*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def language_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not q.data.startswith("lang_"):
        return

    lang_code = q.data.split("_")[1]

    users.update_one(
        {"chat_id": q.message.chat_id},
        {"$set": {"lang": lang_code, "messages": []}},
        upsert=True
    )

    await q.message.reply_text(
        f"✅ Language set!\nNow I’ll reply in *{lang_code.upper()}*.",
        parse_mode="Markdown"
    )

# ---------- CHAT ----------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # 🚫 blocked users ignored
    if is_blocked(user.id):
        return

    text = update.message.text
    doc = users.find_one({"chat_id": chat_id}) or {}

    msgs = doc.get("messages", [])
    lang = doc.get("lang", "en")

    # system prompt (memory start)
    if not msgs:
        msgs.append({
            "role": "system",
            "content": (
                LANG_PROMPTS.get(lang, LANG_PROMPTS["en"]) +
                f" The user's name is {user.first_name}. Remember it."
            )
        })

    msgs.append({"role": "user", "content": text})
    reply = ask_ai(msgs)
    msgs.append({"role": "assistant", "content": reply})

    # save memory
    users.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "chat_id": chat_id,
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "lang": lang,
            "messages": msgs[-20:]
        }},
        upsert=True
    )

    # 👤 TAG + reply-to
    mention = f"[{user.first_name}](tg://user?id={user.id})"
    await update.message.reply_text(
        f"{mention}\n{reply}",
        parse_mode="Markdown",
        reply_to_message_id=update.message.message_id
    )

# ---------- OWNER PANEL ----------
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    await update.message.reply_text(
        f"📊 *OWNER PANEL*\n\n"
        f"👤 Users: {users.count_documents({})}\n"
        f"🚫 Blocked: {blocked.count_documents({'blocked': True})}",
        parse_mode="Markdown"
    )

# ---------- BLOCK / UNBLOCK ----------
async def block_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    target_id = None
    username = None

    if update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        target_id = u.id
        username = u.username
    elif context.args:
        arg = context.args[0]
        if arg.startswith("@"):
            username = arg.lstrip("@")
            doc = users.find_one({"username": username})
            if doc:
                target_id = doc["user_id"]
        else:
            try:
                target_id = int(arg)
            except:
                pass

    if not target_id:
        await update.message.reply_text("Use: /block <user_id> or /block @username or reply")
        return

    blocked.update_one(
        {"user_id": target_id},
        {"$set": {"user_id": target_id, "username": username, "blocked": True}},
        upsert=True
    )

    await update.message.reply_text(
        f"🚫 User blocked: `{target_id}`",
        parse_mode="Markdown"
    )

async def unblock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Use: /unblock <user_id>")
        return
    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("Invalid user ID")
        return

    blocked.delete_one({"user_id": uid})
    await update.message.reply_text(
        f"✅ User unblocked: `{uid}`",
        parse_mode="Markdown"
    )

async def blocked_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    data = list(blocked.find({"blocked": True}))
    if not data:
        await update.message.reply_text("No blocked users.")
        return
    text = "🚫 *Blocked Users:*\n"
    for u in data:
        text += f"- @{u.get('username')} ({u['user_id']})\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= HANDLERS =================
app.add_handler(CommandHandler("language", language_cmd))
app.add_handler(CallbackQueryHandler(language_buttons))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(CommandHandler("block", block_cmd))
app.add_handler(CommandHandler("unblock", unblock_cmd))
app.add_handler(CommandHandler("blocked", blocked_list))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ================= RUN =================
if __name__ == "__main__":
    print("🤖 Bot running in POLLING mode (FINAL)")
    app.run_polling(drop_pending_updates=True)
