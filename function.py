import time

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

# ================= LOGIC FUNCTIONS =================

def check_festival():
    """
    Check karega ki aaj koi festival hai ya nahi.
    Return: Event Name ya None
    """
    today = time.strftime("%d-%m")
    return FESTIVAL_CALENDAR.get(today)

# Future mein aap yahan aur functions add kar sakte ho
# def check_cricket_score():
#     pass
