import requests
import time
import re
import os

# ===== CONFIG (SAFE) =====
TOKEN = os.getenv("BOT_TOKEN")          # Telegram Bot Token (ENV)
CHAT_ID = os.getenv("CHAT_ID")          # Your Chat ID (ENV)
BASE = f"https://api.telegram.org/bot{TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
PRICE_LIMIT = 1020
POLL_DELAY = 2  # seconds

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
})

seen = set()

def send_alert(pid, price):
    product_link = f"shein://product/{pid}"
    coupon_link = "shein://coupon"

    r = requests.post(f"{BASE}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": (
            "⚡ FIRST SHEINVERSE ALERT\n"
            f"💰 Price: ₹{price}\n"
            "👕 Men | Size Ready\n"
            "Tap & Buy Fast 👇"
        ),
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🛒 BUY NOW", "url": product_link},
                {"text": "🎟️ COUPON", "url": coupon_link}
            ]]
        },
        "disable_notification": False
    }).json()

    # Pin message
    if "result" in r:
        mid = r["result"]["message_id"]
        requests.post(f"{BASE}/pinChatMessage", data={
            "chat_id": CHAT_ID,
            "message_id": mid
        })

def check_product(pid):
    try:
        url = f"https://www.sheinindia.in/p/{pid}"
        html = session.get(url, timeout=6).text.lower()

        # PRICE
        pm = re.search(r'₹\s*(\d+)', html)
        if not pm:
            return False
        price = int(pm.group(1))
        if price > PRICE_LIMIT:
            return False

        # CATEGORY
        is_top = any(x in html for x in ["t-shirt", "tshirt", "hoodie", "sweatshirt"])
        is_bottom = any(x in html for x in ["jeans", "pants", "trouser"])

        # SIZE
        if is_top and ('"m"' in html or '"l"' in html):
            return price
        if is_bottom and ('"30"' in html or '"32"' in html):
            return price

    except Exception:
        pass

    return False

while True:
    try:
        html = session.get(COLLECTION_URL, timeout=6).text
        pids = set(re.findall(r'/p/(\d+)', html))

        for pid in pids - seen:
            price = check_product(pid)
            if price:
                send_alert(pid, price)
                seen.add(pid)

    except Exception:
        pass

    time.sleep(POLL_DELAY)
