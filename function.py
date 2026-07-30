USER_WISHED = {}

import random
import pytz
from datetime import datetime

# ================= FESTIVALS =================
FESTIVAL_CALENDAR = {
    "01-01": "🎉 Happy New Year",
    "14-01": "🪁 Happy Makar Sankranti",
    "26-01": "🇮🇳 Happy Republic Day",
    "14-02": "❤️ Happy Valentine's Day",
    "08-03": "🕉️ Happy Mahashivratri",
    "25-03": "🎨 Happy Holi",
    "15-08": "🇮🇳 Happy Independence Day",
    "02-10": "🕊️ Gandhi Jayanti",
    "24-10": "🏹 Happy Dussehra",
    "01-11": "🪔 Happy Diwali",
    "25-12": "🎄 Merry Christmas",
    "31-12": "🎆 Happy New Year's Eve",

    # 🌿 Sawan (30 July 2026)
    "30-07": "🌿 Happy Sawan! Har Har Mahadev 🕉️"
}

# ================= THEMES =================
MORNING_THEMES = [
    "Good Morning ☀️ Positive aur energetic wish karo.",
    "Motivational morning message do.",
    "Smile ke saath din ki shuruaat karne ko bolo.",
    "Fresh aur inspiring greeting do."
]

NOON_THEMES = [
    "Good Afternoon 🌸 Warm aur friendly wish karo.",
    "Productive afternoon ki wish do.",
    "Positive vibes ke saath afternoon greeting do."
]

NIGHT_THEMES = [
    "Good Night 🌙 Sweet dreams wish karo.",
    "Peaceful aur relaxing night wish do.",
    "Kal ke liye motivate karo aur good night bolo."
]


# ================= MAIN FUNCTION =================
def get_bot_extras(user_id, user_name=None):
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    today = now.strftime("%d-%m")
    hour = now.hour

    # Festival sirf ek baar
    event = FESTIVAL_CALENDAR.get(today)
    if event and not USER_WISHED.get(f"{user_id}_{today}"):
        USER_WISHED[f"{user_id}_{today}"] = True
        return f"\n\n{event} 😊"

    # Greeting sirf ek baar per day
    if USER_WISHED.get(f"{user_id}_{today}_greet"):
        return ""

    USER_WISHED[f"{user_id}_{today}_greet"] = True

    if 5 <= hour < 12:
        time_status = "Morning"
        theme = random.choice(MORNING_THEMES)

    elif 12 <= hour < 17:
        time_status = "Afternoon"
        theme = random.choice(NOON_THEMES)

    elif 17 <= hour < 21:
        time_status = "Evening"
        theme = "🌇 Good Evening. Friendly aur positive greeting do."

    else:
        time_status = "Night"
        theme = random.choice(NIGHT_THEMES)

    return (
        f"\n\n⏰ Time: {time_status}"
        f"\nRules:"
        f"\n• Greeting sirf pehle message me do."
        f"\n• Theme: {theme}"
    )
