import requests, time, re, sys, traceback, atexit

# ===== CONFIG =====
TOKEN = "PASTE_TOKEN_IN_VARIABLES"   # ⚠️ Railway Variables me daalo
CHAT_ID = 5480607007
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
last_alive = 0

# ---------- STATUS MESSAGE ----------
def send_status(msg):
    try:
        requests.post(f"{BASE}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg,
            "disable_notification": True
        }, timeout=5)
    except:
        pass

# ---------- EXIT / CRASH INDICATOR ----------
def on_exit():
    send_status("🔴 VIRUS SO GAYA\n⛔ Bot stopped / crashed")

atexit.register(on_exit)

# ---------- DEAL ALERT ----------
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
        }
    }).json()

    if "result" in r:
        requests.post(f"{BASE}/pinChatMessage", data={
            "chat_id": CHAT_ID,
            "message_id": r["result"]["message_id"]
        })

# ---------- PRODUCT CHECK ----------
def check_product(pid):
    try:
        html = session.get(
            f"https://www.sheinindia.in/p/{pid}", timeout=6
        ).text.lower()

        pm = re.search(r'₹\s*(\d+)', html)
        if not pm:
            return False

        price = int(pm.group(1))
        if price > PRICE_LIMIT:
            return False

        is_top = any(x in html for x in ["t-shirt", "tshirt", "hoodie", "sweatshirt"])
        is_bottom = any(x in html for x in ["jeans", "pants", "trouser"])

        if is_top and ('"m"' in html or '"l"' in html):
            return price
        if is_bottom and ('"30"' in html or '"32"' in html):
            return price

    except:
        pass

    return False

# ---------- MAIN BOT ----------
def main():
    global last_alive

    send_status("☠️ 4EDxVirus Active ☠️\n👀 SHEINVERSE pe nazar...")

    while True:
        try:
            html = session.get(COLLECTION_URL, timeout=6).text
            pids = set(re.findall(r'/p/(\d+)', html))

            for pid in pids - seen:
                price = check_product(pid)
                if price:
                    send_alert(pid, price)
                    seen.add(pid)

            # 🔁 Alive ping every 5 minutes
            if time.time() - last_alive > 300:
                send_status("🟢 VIRUS ZINDA HAI\nScanning SHEINVERSE...")
                last_alive = time.time()

        except Exception as e:
            send_status("⚠️ BOT ERROR\nRestarting loop...")
            time.sleep(5)

        time.sleep(POLL_DELAY)

# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    main()
