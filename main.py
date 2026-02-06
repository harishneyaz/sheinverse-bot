import requests
import time
import random
import json
import os
from datetime import datetime

# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

SHEIN_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
DATA_FILE = "data.json"

CHECK_MIN = 30      # 30 sec rapid mode
SUMMARY_INTERVAL = 60 * 60 * 2  # 2 hours

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
# ==========================================


def send_telegram(msg, image=None, link=None):
    if image:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": msg
        }
        files = {"photo": image}
        requests.post(url, data=payload, files=files)
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


def load_old_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def fetch_products():
    # Shein internal JSON endpoint (listing)
    api = "https://www.sheinindia.in/api/product/list"
    params = {
        "cat_id": "37961",
        "page": 1,
        "limit": 100
    }

    r = requests.get(api, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()["data"]["products"]


def filter_men(products):
    men = []
    women = []

    for p in products:
        cat = p.get("gender", "").lower()
        if "men" in cat:
            men.append(p)
        else:
            women.append(p)

    return men, women


def startup_summary(men, women):
    msg = (
        "🤖 SHEIN Verse Bot Started\n\n"
        f"👔 MEN Available: {len(men)}\n"
        f"👗 WOMEN Available: {len(women)}\n\n"
        "Monitoring MEN stock only 🔥"
    )
    send_telegram(msg)


def stock_check():
    old_data = load_old_data()
    products = fetch_products()

    men, women = filter_men(products)

    for p in men:
        pid = str(p["id"])
        stock = p.get("stock", 0)
        name = p.get("name")
        price = p.get("price")
        image = p.get("image")
        link = "https://www.sheinindia.in" + p.get("url")

        old_stock = old_data.get(pid, 0)

        if stock > 0 and old_stock == 0:
            msg = (
                "🔥 MEN STOCK ALERT 🔥\n\n"
                f"Product: {name}\n"
                f"Price: ₹{price}\n"
                "Status: AVAILABLE ✅\n\n"
                f"🛒 Buy Now:\n{link}"
            )
            send_telegram(msg, image=image)

        old_data[pid] = stock

    save_data(old_data)
    return len(men), len(women)


def summary_message(men_count):
    msg = (
        "⏰ 2 Hour Update — SHEIN Verse\n\n"
        f"👔 MEN Available: {men_count}\n"
        f"Last check: {datetime.now().strftime('%H:%M:%S')}\n\n"
        "Bot running ✅"
    )
    send_telegram(msg)


# ================= MAIN LOOP =================
if __name__ == "__main__":
    last_summary = 0

    products = fetch_products()
    men, women = filter_men(products)
    startup_summary(men, women)

    while True:
        try:
            men_count, women_count = stock_check()

            if time.time() - last_summary > SUMMARY_INTERVAL:
                summary_message(men_count)
                last_summary = time.time()

            time.sleep(CHECK_MIN)

        except Exception as e:
            time.sleep(10)
