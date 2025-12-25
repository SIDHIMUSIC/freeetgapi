import requests
import re 
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
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
SUPPORT_CHANNEL = "https://t.me/TG_BIO_STYLE"

MODEL = "deepseek/deepseek-chat"

if not all([TOKEN, OPENROUTER_KEY, MONGO_URI, OWNER_ID]):
    raise RuntimeError("Missing ENV variables")

# ================= DB =================
db = MongoClient(MONGO_URI)["telegram_bot"]
users = db.users
bot_bans = db.bot_bans
ban_logs = db.ban_logs
spam = db.spam
chat_logs = db.chat_logs
badwords = db.badwords

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

# ================= LOG EVERY MESSAGE =================
async def log_message(update, context):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    text = update.message.text

    log_text = (
        f"📩 NEW MESSAGE\n\n"
        f"👤 Name: {user.first_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"💬 Chat ID: {chat.id}\n"
        f"📍 Chat Type: {chat.type}\n"
        f"🕒 Time: {time.strftime('%d-%m-%Y %H:%M:%S')}\n\n"
        f"📝 Message:\n{text}"
    )

    # send to log group
    if LOG_GROUP_ID:
        try:
            await context.bot.send_message(LOG_GROUP_ID, log_text)
        except:
            pass

    # save to MongoDB
    chat_logs.insert_one({
        "user_id": user.id,
        "name": user.first_name,
        "username": user.username,
        "chat_id": chat.id,
        "chat_type": chat.type,
        "text": text,
        "time": time.time()
    })

# ================= AI =================
def safe_ai(messages):
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/SANATANI_BACHA",
                "X-Title": "Telegram AI Bot"
            },
            json={
                "model": MODEL,
                "messages": messages
            },
            timeout=60
        )

        data = r.json()

        # 👇 DEBUG (Railway logs me dikhega)
        print("OPENROUTER RESPONSE:", data)

        if "choices" not in data:
            return "⚠️ AI response error. Thodi der baad try karo."

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI ERROR:", e)
        return "🙂 Abhi thodi dikkat aa rahi hai, baad me try karo."
# ================= TYPING =================
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
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌍 Language", callback_data="open_lang")],
            [InlineKeyboardButton("❖ Help ❖", callback_data="help_back")],
            [InlineKeyboardButton("❖ Support ❖", url=SUPPORT_CHANNEL)],
        ]
    )

    await update.message.reply_photo(
        photo=random.choice(START_IMAGES),
        caption=(
            f"👋🫶 Hi {update.effective_user.first_name}\n"
            "🤖 Smart AI Bot Ready"
        ),
        reply_markup=kb
    )

# ================= help =================
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

HELP_TEXT = (
    "🤖 <b>BOT FULL FUNCTION LIST</b>\n"
    "━━━━━━━━━━━━━━━━━━\n\n"

    "<b>Basic Commands</b>\n"
    "/start – Bot start\n"
    "/help – All functions\n"
    "/id – User & Chat ID\n"
    "/language – Hindi / English\n\n"

    "<b>AI Image</b>\n"
    "/image &lt;prompt&gt; – AI Image\n\n"

    "<b>Auto Replies</b>\n"
    "• joke / funny → Joke\n"
    "• shayari / love / sad → Shayari\n"
    "• GM / GN → Auto Reply\n"
    "• 18+ / Gaali → Auto Filter\n\n"

    "<b>Admin</b>\n"
    "/ban\n"
    "/unban\n\n"

    "<b>Owner</b>\n"
    "/botban &lt;id&gt;\n"
    "/botunban &lt;id&gt;\n"
    "/stats\n\n"

    "<b>System</b>\n"
    "❖ Tag reply\n"
    "❖ Typing ON\n"
    "❖ Logs ON\n"
    "❖ Memory ON\n\n"

    "<b>Bad Word Filter</b>\n"
    "/addbadword &lt;word&gt;\n"
    "/removebadword &lt;word&gt;\n\n"

    "👇 <i>Use buttons below for category-wise help</i>"
)

# /help command
async def help_cmd(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📌 Basic", callback_data="help_basic"),
                InlineKeyboardButton("🖼 AI Image", callback_data="help_image"),
            ],
            [
                InlineKeyboardButton("🤖 Auto", callback_data="help_auto"),
                InlineKeyboardButton("🛡 Admin", callback_data="help_admin"),
            ],
            [
                InlineKeyboardButton("👑 Owner", callback_data="help_owner"),
                InlineKeyboardButton("❌ Close", callback_data="help_close"),
            ],
        ]
    )

    # ✅ ALWAYS send a NEW message (photo-safe)
    if update.callback_query:
        await update.callback_query.message.reply_text(
            HELP_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            HELP_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

# help buttons callback
async def help_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help_basic":
        text = (
            "📌 <b>BASIC COMMANDS</b>\n\n"
            "/start\n/help\n/id\n/language"
        )

    elif data == "help_image":
        text = (
            "🖼 <b>AI IMAGE</b>\n\n"
            "/image &lt;prompt&gt;\n"
            "<code>/image lord krishna digital art</code>"
        )

    elif data == "help_auto":
        text = (
            "🤖 <b>AUTO FEATURES</b>\n\n"
            "Joke\nShayari\nGM / GN\n18+ / Gaali Filter"
        )

    elif data == "help_admin":
        text = (
            "🛡 <b>ADMIN COMMANDS</b>\n\n"
            "/ban\n/unban\n"
            "/addbadword &lt;word&gt;\n"
            "/removebadword &lt;word&gt;"
        )

    elif data == "help_owner":
        text = (
            "👑 <b>OWNER COMMANDS</b>\n\n"
            "/botban &lt;id&gt;\n"
            "/botunban &lt;id&gt;\n"
            "/stats"
        )

    elif data == "help_back":
        await help_cmd(update, context)
        return

    elif data == "help_close":
        await query.message.delete()
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅ Back", callback_data="help_back"),
                InlineKeyboardButton("❌ Close", callback_data="help_close"),
            ]
        ]
    )

    # ✅ ALWAYS SEND NEW MESSAGE (NO edit_text)
    await query.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
# ================= LANGUAGE =================
async def language(update, context):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇮🇳 Hindi", callback_data="hi"),
         InlineKeyboardButton("🇬🇧 English", callback_data="en")]
    ])
    await update.effective_message.reply_text("Choose language:", reply_markup=kb)

async def lang_cb(update, context):
    q = update.callback_query
    await q.answer()

    if q.data == "open_lang":
        await language(update, context)
        return

    users.update_one(
        {"user_id": q.from_user.id},
        {"$set": {"lang": q.data}},
        upsert=True
    )
    await q.message.reply_text("❍ Language set❍")

# ================= IMAGE =================
async def image_cmd(update, context):
    if not context.args:
        return await update.message.reply_text(
            "❌ Use like:\n/image cyberpunk indian boy 4k"
        )

    prompt = " ".join(context.args)

    # typing / uploading effect
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="upload_photo"
    )

    image_url = (
        "https://image.pollinations.ai/prompt/"
        + requests.utils.quote(prompt)
        + "?width=1024&height=1024&seed=42&model=flux"
    )

    try:
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🖼 Prompt:\n{prompt}"
        )
    except Exception:
        await update.message.reply_text(
            "❌ Image generate nahi ho pa rahi.\n"
            "Simple prompt try karo."
        )

# ================= AUTO MOD =================
BAD_WORDS = ["spamword1", "spamword2"]

BAD_WORDS.extend([
    # English 18+
    "fuck", "fucker", "sex", "porn", "nude", "xxx",
    "boobs", "asshole", "bitch", "slut", "dick", "pussy",
    "blowjob", "handjob", "anal", "rape",

    # Hindi gaali
    "chutiya", "madarchod", "bhosdike", "lund", "gaand", "randi",
    "bhenchod", "behenchod", "mc", "bc", "saala", "harami",
    "chod", "chodu", "gandu", "kamina"
])

def get_bad_words():
    words = set(BAD_WORDS)
    for w in badwords.find():
        words.add(w["word"])
    return list(words)

async def auto_mod(update, context):
    if not update.message or not update.message.text:
        return

    # 🔥 COMMANDS KO AUTO-MOD SE SKIP KARO
    if update.message.text.startswith("/"):
        return

    text = update.message.text.lower()
    uid = update.effective_user.id

    # 🔹 GAALI / 18+ CHECK
    for word in get_bad_words():
        if re.search(rf"\b{re.escape(word)}\b", text):
            try:
                await update.message.delete()
                await update.message.reply_text(
                    "🚫 Gali / 18+ content allowed nahi hai"
                )
            except:
                pass
            return

    # 🔹 SPAM CHECK
    last = spam.find_one({"user": uid})
    now = time.time()

    if last and now - last.get("time", 0) < 3:
        await update.message.reply_text("⚠️ Spam mat karo")
        return

    spam.update_one({"user": uid}, {"$set": {"time": now}}, upsert=True)
# ================= BADWORD COMMANDS =================
async def addbadword(update, context):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        return await update.message.reply_text("/addbadword <word>")
    word = context.args[0].lower()
    if badwords.find_one({"word": word}):
        return await update.message.reply_text("⚠️ Word already added")
    badwords.insert_one({"word": word, "time": time.time()})
    await update.message.reply_text(f"❍ Added badword❍: `{word}`", parse_mode="Markdown")

async def removebadword(update, context):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        return await update.message.reply_text("/removebadword <word>")
    word = context.args[0].lower()
    res = badwords.delete_one({"word": word})
    if res.deleted_count == 0:
        return await update.message.reply_text("⚠️ Word not found")
    await update.message.reply_text(f"✅ Removed badword: `{word}`", parse_mode="Markdown")
# ================= BAN SYSTEM =================

# 🔹 OWNER – GLOBAL BOT BAN
async def botban(update, context):
    if not is_owner(update.effective_user.id):
        return

    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text(
            "❌ Use: /botban <user_id>"
        )

    uid = int(context.args[0])
    bot_bans.update_one(
        {"user_id": uid},
        {"$set": {"user_id": uid}},
        upsert=True
    )
    await update.message.reply_text("🚫 User globally bot-banned")


# 🔹 OWNER – GLOBAL BOT UNBAN
async def botunban(update, context):
    if not is_owner(update.effective_user.id):
        return

    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text(
            "❌ Use: /botunban <user_id>"
        )

    uid = int(context.args[0])
    bot_bans.delete_one({"user_id": uid})
    await update.message.reply_text("✅ User globally unbanned 🫶")


# 🔹 GROUP ADMIN – BAN
async def ban(update, context):
    if not await is_admin(update, context):
        return

    uid = None
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
    elif context.args and context.args[0].isdigit():
        uid = int(context.args[0])

    if not uid:
        return await update.message.reply_text(
            "❌ Reply to a user or use: /ban <user_id>"
        )

    await context.bot.ban_chat_member(update.effective_chat.id, uid)
    await update.message.reply_text("🚫 User banned from group")


# 🔹 GROUP ADMIN – UNBAN
async def unban(update, context):
    if not await is_admin(update, context):
        return

    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text(
            "❌ Use: /unban <user_id>"
        )

    uid = int(context.args[0])
    await context.bot.unban_chat_member(update.effective_chat.id, uid)
    await update.message.reply_text("✅ User unbanned from group")

# ================= CHAT =================
async def chat(update, context):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    text = update.message.text.lower()

    if is_bot_banned(user.id):
        return

    # 🔥 STEP 1: LOG USER MESSAGE
    await log_message(update, context)

    # 🔥 STEP 2: AUTO MOD
    await auto_mod(update, context)

    # 🔥 STEP 3: SAVE USER
    users.update_one(
        {"user_id": user.id},
        {"$set": {
            "first_name": user.first_name,
            "username": user.username,
            "last_seen": time.time()
        }},
        upsert=True
    )

    # 🔥 STEP 4: AI SYSTEM PROMPT
    if "joke" in text or "funny" in text or "hasi" in text:
        system = "Tell a short funny joke in Hinglish with emojis."
    elif "shayari" in text or "love" in text or "sad" in text:
        system = "Write a beautiful Hindi shayari with emojis."
    else:
        system = f"Chat naturally with user named {user.first_name}."

    # 🔥 STEP 5: AI REPLY
    reply = safe_ai([
        {"role": "system", "content": system},
        {"role": "user", "content": update.message.text}
    ])

    mention = f"[{user.first_name}](tg://user?id={user.id})"
    final_reply = f"{mention}\n{reply}"
    
# 🔐 STEP 5.5: TELEGRAM TEXT LIMIT FIX (⭐ MOST IMPORTANT ⭐)
    MAX_LEN = 4000
    if len(final_reply) > MAX_LEN:
        final_reply = final_reply[:MAX_LEN]
        
    # 🔥 STEP 6: SEND BOT MESSAGE (ONLY ONCE)
    await typing_reply(update, context, final_reply)

    # 🔥 STEP 7: LOG BOT REPLY (OPTIONAL)
    chat_logs.insert_one({
        "user_id": user.id,
        "name": user.first_name,
        "username": user.username,
        "chat_id": update.effective_chat.id,
        "chat_type": update.effective_chat.type,
        "text": f"[BOT_REPLY]\n{reply}",
        "time": time.time()
    })

# ================= STATS =================
async def stats(update, context):
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Owner only command")

    total_users = users.count_documents({})
    total_banned = bot_bans.count_documents({})

    # unique groups
    total_groups = len(
        chat_logs.distinct(
            "chat_id", {"chat_type": {"$in": ["group", "supergroup"]}}
        )
    )

    # daily active users (last 24 hours)
    since = time.time() - 86400
    daily_active = len(
        chat_logs.distinct("user_id", {"time": {"$gte": since}})
    )

    await update.message.reply_text(
        f"📊 **BOT DASHBOARD**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"🔥 Daily Active Users: `{daily_active}`\n"
        f"👨‍👩‍👧‍👦 Total Groups: `{total_groups}`\n"
        f"🚫 Bot Banned Users: `{total_banned}`",
        parse_mode="Markdown"
    )
    # ================= ID COMMAND =================
async def id_cmd(update, context):
    user = update.effective_user
    chat = update.effective_chat

    text = (
        f"👤 **Your ID:** `{user.id}`\n"
        f"💬 **Chat ID:** `{chat.id}`\n"
        f"📍 **Chat Type:** `{chat.type}`"
    )

    await update.message.reply_text(text, parse_mode="Markdown")
    # ================= BROADCAST (TELEGRAM ONLY) =================
async def broadcast(update, context):
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Owner only command")

    if not context.args:
        return await update.message.reply_text(
            "❌ Use:\n/broadcast Your message here"
        )

    msg = " ".join(context.args)

    sent = 0
    failed = 0

    await update.message.reply_text("📤 Broadcast start ho raha hai...")

    for u in users.find({}, {"user_id": 1}):
        try:
            await context.bot.send_message(
                chat_id=u["user_id"],
                text=msg
            )
            sent += 1
            await asyncio.sleep(0.05)  # anti-flood (IMPORTANT)
        except:
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast complete\n\n"
        f"📨 Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )
    
# ================= OWNER =================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def owner_info(update, context):
    owner_name = "𓆩◕🇭𝐀𝐑𝐑𝐘◕𓆪 =‌𐏓 𝄗⃝🇮🇳™"
    owner_username = "SANATANI_BACHA"

    text = (
        "<b>👑 ʙᴏᴛ ᴏᴡɴᴇʀ ᴘʀᴏғɪʟᴇ✨</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "✨ ᴛʜɪs ɪɴᴛᴇʟʟɪɢᴇɴᴛ ᴀɪ ʙᴏᴛ ɪs ᴘʀᴏᴜᴅʟʏ ᴄʀᴀғᴛᴇᴅ,\n"
        "ᴏᴡɴᴇᴅ ᴀɴᴅ ᴍᴀɴᴀɢᴇᴅ ʙʏ\n\n"

        f"👤 <b><a href='https://t.me/{owner_username}'>{owner_name}</a></b>\n"
        f"🔗 @{owner_username}\n\n"

        "🚀 ᴀ ᴘᴀssɪᴏɴᴀᴛᴇ ᴅᴇᴠᴇʟᴏᴘᴇʀ & ᴛᴇᴄʜ ᴇɴᴛʜᴜsɪᴀsᴛ\n"
        "• sᴍᴀʀᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴏɴ 🤖\n"
        "• sᴇᴄᴜʀᴇ sʏsᴛᴇᴍs 🔐\n"
        "• sᴍᴏᴏᴛʜ ᴜsᴇʀ ᴇxᴘᴇʀɪᴇɴᴄᴇ 💎\n\n"

        "💡 ᴠɪsɪᴏɴ\n"
        "ᴄʀᴇᴀᴛɪɴɢ ᴘᴏᴡᴇʀғᴜʟ, ʀᴇʟɪᴀʙʟᴇ ᴀɴᴅ\n"
        "ᴜsᴇʀ-ғʀɪᴇɴᴅʟʏ ᴀɪ ʙᴏᴛs\n"
        "ᴛʜᴀᴛ ᴍᴀᴋᴇ ᴛᴇʟᴇɢʀᴀᴍ sᴍᴀʀᴛᴇʀ ⚡\n\n"

        "👇 ᴄᴏɴɴᴇᴄᴛ & sᴛᴀʏ ᴜᴘᴅᴀᴛᴇᴅ"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="❍ 𝐎ᴡɴᴇʀ ❍",
                    url=f"https://t.me/{owner_username}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❍ Support Channel ❍",
                    url=SUPPORT_CHANNEL
                )
            ]
        ]
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# ================= STIKCER ID =================
#async def sticker_id(update, context):
#    if update.message.sticker:
 #       await update.message.reply_text(
     #       f"Sticker ID:\n<code>{update.message.sticker.file_id}</code>",
     #       parse_mode="HTML"
       # )
# ================= APP =================
app = ApplicationBuilder().token(TOKEN).build()

# 1️⃣ COMMANDS
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("language", language))
app.add_handler(CommandHandler("image", image_cmd))
app.add_handler(CommandHandler("owner", owner_info))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("botban", botban))
app.add_handler(CommandHandler("botunban", botunban))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("id", id_cmd))
app.add_handler(CommandHandler("addbadword", addbadword))
app.add_handler(CommandHandler("removebadword", removebadword))
app.add_handler(CommandHandler("broadcast", broadcast))

# 2️⃣ CALLBACK BUTTONS (IMPORTANT ORDER)
app.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
app.add_handler(CallbackQueryHandler(lang_cb, pattern="^(open_lang|hi|en)$"))
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
# 3️⃣ LOGS — SABSE PEHLE
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

# 5️⃣ MAIN AI CHAT — LAST
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

# 6️⃣ STICKER HANDLER (OPTIONAL)
#app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_id))

print("🤖 BOT STARTED BY HARRY TG @SANATANI_BACHA")

app.run_polling(
    drop_pending_updates=True,
    allowed_updates=Update.ALL_TYPES
)
