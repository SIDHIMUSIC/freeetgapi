import time
import random

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

# ================= 2. CREATIVE THEMES (Har baar kuch naya) =================
MORNING_THEMES = [
    "ek motivational quote ke saath Good Morning wish karo.",
    "ek funny lazy morning joke ke saath uthao.",
    "kisi positive fact ya wisdom ke saath din ki shuruwat karo.",
    "ek khoobsurat Hindi shayari ke saath Good Morning bolo.",
    "pure energetic aur excitement ke saath Good Morning bolo."
]

NOON_THEMES = [
    "user se pucho lunch kiya ya nahi, thoda caring style mein.",
    "ek chota sa funny remark maaro ki 'neend aa rahi hai kya?'.",
    "batao ki aadha din khatam ho gaya, baaki aadha full power mein nikaalo.",
    "thoda sarcasm use karo ki 'kaam kar rahe ho ya time pass?'."
]

NIGHT_THEMES = [
    "din bhar ki thakan mitane wali ek sukoon bhari baat bolo.",
    "ek deep meaningful thought ya shayari ke saath Good Night bolo.",
    "pucho ki 'aaj ka din kaisa gaya?' friendly style mein.",
    "mazaak mein bolo ki 'phone rakh do aur so jao'."
]

# ================= 3. MAIN LOGIC (FIXED NAME & ARGUMENT) =================

def get_bot_extras(user_name=None):
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    today = now.strftime("%d-%m")
    hour = now.hour

    # FESTIVAL CHECK
    event_name = FESTIVAL_CALENDAR.get(today)
    if event_name:
        return (
            f"\n\n🎉 SPECIAL EVENT: Aaj '{event_name}' hai!"
            f"\n🤖 Rule: Sirf greeting pe hi wish karna."
        )

    # TIME LOGIC
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
        f"\n3. Normal sawal pe wish mat repeat karo."
    )
