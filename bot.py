LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
import os, requests, random, asyncio, time
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================= ENV =================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_CHANNEL = "https://t.me/TG_BIO_STYLE"

if not all([TOKEN, OPENROUTER_KEY, MONGO_URI, OWNER_ID]):
    raise RuntimeError("Missing ENV variables")

MODEL = "deepseek/deepseek-chat"

# ================= DB =================
db = MongoClient(MONGO_URI)["telegram_bot"]
users = db.users
bot_bans = db.bot_bans
ban_logs = db.ban_logs
spam = db.spam

# ================= HELPERS =================
def is_owner(uid): 
    return uid == OWNER_ID

def is_bot_banned(uid): 
    return bot_bans.find_one({"user_id": uid}) is not None

async def is_admin(update, context):
    if update.effective_chat.type == "private":
        return False
    m = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return m.status in ("administrator", "creator")
    # ================= HELPERS =================
def is_owner(uid): 
    return uid == OWNER_ID

def is_bot_banned(uid): 
    return bot_bans.find_one({"user_id": uid}) is not None

async def is_admin(update, context):
    if update.effective_chat.type == "private":
        return False
    m = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return m.status in ("administrator", "creator")


# ================= LOG HELPER =================
async def send_log(context, text):
    if LOG_GROUP_ID == 0:
        return
    try:
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=text,
            parse_mode="Markdown"
        )
    except Exception:
        pass

# ================= AI =================
def safe_ai(messages):
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={"model": MODEL, "messages": messages},
            timeout=60
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return "🙂 Abhi thodi dikkat aa rahi hai, baad me try karo."

async def typing_reply(update, context, text):
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await asyncio.sleep(0.4)
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= START =================
START_IMAGES = [
    "https://graph.org/file/705cda02e63f4cb0bdb90-ce4d0ddd3a8cf38b5a.jpg",
    "https://graph.org/file/8c5e8ea95b69e682aed19-22090eb6bb17ce7a54.jpg",
    "https://graph.org/file/556615482003de63f32be-58c192c7e65004f9d4.jpg",
    "https://graph.org/file/bb129887cac5752f0f0f5-70aec0f85376516f16.jpg"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Language", callback_data="open_lang")],
        [InlineKeyboardButton("📢 Support Channel", url=SUPPORT_CHANNEL)]
    ])
    await update.message.reply_photo(
        photo=random.choice(START_IMAGES),
        caption=(
            f"👋 Hi {update.effective_user.first_name}!\n\n"
            "🤖 Main ek smart AI bot hoon.\n"
            "💬 Chat • 😂 Joke • ✍️ Shayari • 🖼 Image\n\n"
            "👇 owner @SANATANI_BACHA 👑"
        ),
        reply_markup=kb
    )

# ================= LANGUAGE =================
async def language(update, context):
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇮🇳 Hindi", callback_data="hi"),
            InlineKeyboardButton("🇬🇧 English", callback_data="en")
        ]
    ])
    if update.message:
        await update.message.reply_text("Choose language:", reply_markup=kb)
    else:
        await update.callback_query.message.reply_text("Choose language:", reply_markup=kb)

async def lang_cb(update, context):
    q = update.callback_query
    await q.answer()

    if q.data == "open_lang":
        await language(update, context)
        return

    if q.data in ("hi", "en"):
        users.update_one(
            {"chat_id": q.message.chat_id},
            {"$set": {"lang": q.data}},
            upsert=True
        )
        await q.message.reply_text("✅ Language set")

# ================= OWNER BOT BAN =================
async def botban(update, context):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        return
    uid = int(context.args[0])
    bot_bans.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
    await update.message.reply_text("🚫 User bot-banned")

async def botunban(update, context):
    if not is_owner(update.effective_user.id):
        return
    uid = int(context.args[0])
    bot_bans.delete_one({"user_id": uid})
    await update.message.reply_text("✅ User bot-unbanned")

# ================= GROUP BAN =================
async def ban(update, context):
    if not await is_admin(update, context):
        return

    uid = None
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
    elif context.args and context.args[0].isdigit():
        uid = int(context.args[0])

    if not uid:
        return

    await context.bot.ban_chat_member(update.effective_chat.id, uid)
    ban_logs.insert_one({
        "chat_id": update.effective_chat.id,
        "user_id": uid,
        "time": time.time()
    })
    await update.message.reply_text("🚫 User banned")

async def unban(update, context):
    if not await is_admin(update, context):
        return
    if not context.args:
        return
    uid = int(context.args[0])
    await context.bot.unban_chat_member(update.effective_chat.id, uid)
    await update.message.reply_text("✅ User unbanned")

# ================= AUTO MOD =================
BAD_WORDS = ["spamword1", "spamword2"]

async def auto_mod(update, context):
    text = update.message.text.lower()
    uid = update.effective_user.id

    if any(w in text for w in BAD_WORDS):
        await update.message.delete()
        return

    last = spam.find_one({"user": uid})
    if last and time.time() - last["time"] < 3:
        await update.message.reply_text("⚠️ Spam mat karo")
    spam.update_one({"user": uid}, {"$set": {"time": time.time()}}, upsert=True)

# ================= CHAT =================
async def chat(update, context):
    user = update.effective_user

    if is_bot_banned(user.id):
        return

    await auto_mod(update, context)

    chat_id = update.effective_chat.id
    doc = users.find_one({"chat_id": chat_id}) or {}
    msgs = doc.get("messages", [])
    lang = doc.get("lang", "en")

    if not msgs:
        msgs.append({
            "role": "system",
            "content": (
                f"The user's name is {user.first_name}. "
                "Reply like a human. "
                "Use the user's name sometimes. "
                "Use emojis only when they naturally fit."
            )
        })

    msgs.append({"role": "user", "content": update.message.text})
    reply = safe_ai(msgs)
    msgs.append({"role": "assistant", "content": reply})

    users.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "chat_id": chat_id,
            "user_id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "lang": lang,
            "messages": msgs[-20:]
        }},
        upsert=True
    )

    mention = f"[{user.first_name}](tg://user?id={user.id})"
    await typing_reply(update, context, f"{mention}\n{reply}")

# ================= APP =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("language", language))
app.add_handler(CallbackQueryHandler(lang_cb))
app.add_handler(CommandHandler("botban", botban))
app.add_handler(CommandHandler("botunban", botunban))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 BOT RUNNING (FINAL)")
app.run_polling(drop_pending_updates=True)
