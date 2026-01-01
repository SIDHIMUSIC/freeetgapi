import time
import random

# ================= 1. CALENDAR DATA =================
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

# ================= 3. MAIN LOGIC (SMART GREETING) =================

def get_daily_prompt():
    """
    Ye function AI ko strictly batayega ki:
    - Sirf start mein wish karo.
    - Baar-baar repeat mat karo.
    """
    
    # --- 1. FESTIVAL CHECK ---
    today = time.strftime("%d-%m")
    event_name = FESTIVAL_CALENDAR.get(today)

    if event_name:
        return (
            f"\n\n🎉 SPECIAL EVENT: Aaj '{event_name}' hai! "
            f"\n🤖 **RULE:** Agar user ne **Greeting (Hi/Hello)** kiya hai, tabhi usko '{event_name}' wish karna."
            f" Agar wo normal sawaal puch raha hai, to baar-baar wish mat karna."
        )

    # --- 2. TIME CHECK (GM/GN Logic) ---
    hour = int(time.strftime("%H")) # Current Hour (0-23)

    if 5 <= hour < 12:
        time_status = "Morning"
        theme = random.choice(MORNING_THEMES)
        
    elif 12 <= hour < 17:
        time_status = "Afternoon"
        theme = random.choice(NOON_THEMES)
        
    elif 17 <= hour < 20:
        time_status = "Evening"
        theme = "ek fresh evening tea/coffee wali vibe ke saath wish karo."
        
    else:
        time_status = "Night"
        theme = random.choice(NIGHT_THEMES)

    # --- 3. FINAL INSTRUCTION (ANTI-REPETITION) ---
    return (
        f"\n\n⏰ TIME CONTEXT: Abhi '{time_status}' ka time hai."
        f"\n🤖 **STRICT INSTRUCTION:**"
        f"\n1. **Sirf Tabhi Wish Karo:** Jab user ne conversation start ki ho (Hi, Hello, GM, GN, Start bola ho)."
        f"\n2. **Theme Use Karo:** Agar wish kar rahe ho, to ye theme use karna: '{theme}'"
        f"\n3. **NO REPEAT:** Agar user koi sawal puch raha hai ya normal baat kar raha hai, to 'Good {time_status}' bolne ki zaroorat nahi hai. Seedha jawab do."
    )
    
