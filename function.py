import time
import random
import pytz
from datetime import datetime
# ================= 1. CALENDAR DATA =================
FESTIVAL_CALENDAR = {
    "01-01": "Happy New Year  🎉",
    "14-01": "Makar Sankranti 🪁",
    "26-01": "Happy Republic Day 🇮🇳",
    "14-02": "Valentine's Day ❤️",
    "08-03": "Mahashivratri 🕉️",
    "25-03": "Happy Holi 🎨",
    "15-08": "Independence Day 🇮🇳",
    "02-10": "Gandhi Jayanti 🕊️",
    "24-10": "Happy Dussehra 🏹",
    "01-11": "Happy Diwali 🪔",
    "25-12": "Merry Christmas 🎄",
    "31-12": "New Year's Eve 🎆"
}



# ================= 3. MAIN LOGIC (FIXED NAME & ARGUMENT) =================
def get_bot_extras(user_id, user_name=None):
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    today = now.strftime("%d-%m")
    hour = now.hour

    # ❌ Agar already wish ho chuki hai → kuch mat bhejo
    if USER_WISHED.get(user_id):
        return ""

    # 🎉 FESTIVAL CHECK (SIRF PEHLI BAAR)
    event_name = FESTIVAL_CALENDAR.get(today)
    if event_name:
        USER_WISHED[user_id] = True
        return f"\n\n🪁 {event_name} ki hardik shubhkamnayein 😊"

    # ⏰ TIME BASED GREETING (SIRF PEHLI BAAR)
    USER_WISHED[user_id] = True

    if 5 <= hour < 12:
        time_status = "Morning"
        theme = random.choice(MORNING_THEMES)

    elif 12 <= hour < 17:
        time_status = "Afternoon"
        theme = random.choice(NOON_THEMES)

    elif 17 <= hour < 21:
        time_status = "Evening"
        theme = "ek fresh evening tea/coffee wali vibe ke saath wish karo."

    else:
        time_status = "Night"
        theme = random.choice(NIGHT_THEMES)

    return (
        f"\n\n⏰ TIME CONTEXT: Abhi '{time_status}' ka time hai."
        f"\n🤖 Rules:"
        f"\n1. Greeting pe hi wish karo."
        f"\n2. Theme use karo: '{theme}'."
    )
