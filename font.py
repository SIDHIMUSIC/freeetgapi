from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# ================= FONT MAP =================
FONT_MAP = {
    "bold": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
    ),
    "smallcaps": str.maketrans(
        "abcdefghijklmnopqrstuvwxyz",
        "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    ),
    "circle": str.maketrans(
        "abcdefghijklmnopqrstuvwxyz",
        "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ"
    ),
}
#converter 
def convert_font(text: str, style: str) -> str:
    table = FONT_MAP.get(style)
    if not table:
        return text
    return text.translate(table)
#menu function 


async def send_font_menu(update, context):
    text = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("Bold", callback_data=f"font|bold"),
            InlineKeyboardButton("Small Caps", callback_data=f"font|smallcaps"),
        ],
        [
            InlineKeyboardButton("Circle", callback_data=f"font|circle"),
        ]
    ]

    context.user_data["font_text"] = text

    await update.message.reply_text(
        "👇 Choose font style:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

#callback
async def font_callback(update, context):
    query = update.callback_query
    await query.answer()

    _, style = query.data.split("|")
    text = context.user_data.get("font_text", "")

    styled = convert_font(text, style)
    await query.message.reply_text(styled)
