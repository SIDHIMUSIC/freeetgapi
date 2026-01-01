import time
import random

# ================= CALENDAR DATA =================
FESTIVAL_CALENDAR = {
    "01-01": "Happy New Year 2026 🎉",
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

# ================= CREATIVE THEMES (Har baar kuch naya) =================
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

def get_daily_prompt():
    """
    Ye function:
    1. Pehle Festival check karega.
    2. Agar Festival nahi hai, to Time check karega.
    3. Time ke hisaab se Random Theme pick karega.
    """
    
    # --- 1. FESTIVAL CHECK ---
    today = time.strftime("%d-%m")
    event_name = FESTIVAL_CALENDAR.get(today)

    if event_name:
        return (
            f"\n\n🎉 SPECIAL EVENT: Aaj '{event_name}' hai! "
            f"Apne reply ki shuruwat '{event_name}' wish karke hi karna. "
            f"Wish ekdum creative aur dil se honi chahiye (Shayari/Emoji use karo)."
        )

    # --- 2. TIME CHECK (GM/GN Logic) ---
    hour = int(time.strftime("%H")) # Current Hour (0-23)

    if 5 <= hour < 12:  # Subah 5 se 12 baje tak
        time_status = "Morning"
        theme = random.choice(MORNING_THEMES)
        
    elif 12 <= hour < 17:  # Dopahar 12 se 5 baje tak
        time_status = "Afternoon"
        theme = random.choice(NOON_THEMES)
        
    elif 17 <= hour < 20:  # Shaam 5 se 8 baje tak
        time_status = "Evening"
        theme = "ek fresh evening tea/coffee wali vibe ke saath wish karo."
        
    else:  # Raat 8 baje ke baad (ya Subah 5 se pehle)
        time_status = "Night"
        theme = random.choice(NIGHT_THEMES)

    # --- 3. FINAL INSTRUCTION FOR AI ---
    return (
        f"\n\n⏰ TIME UPDATE: Abhi '{time_status}' ka time hai. "
        f"Agar user ne greeting (Hi/Hello) kiya hai, to usko '{theme}' "
        f"Bas 'Good {time_status}' mat bolna, kuch creative likhna."
    )
    
