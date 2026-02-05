import requests, time, re, os, atexit

# ===== ENV CONFIG =====
TOKEN = os.getenv("TOKEN")           # Railway Variables me daalo
CHAT_ID = int(os.getenv("CHAT_ID"))  # Telegram ID
BASE = f"https://api.telegram.org/bot{TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
PRICE_LIMIT = 1020
POLL_DELAY = 1  # ultra-fast

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
})

seen_products = set()   # pid -> sent alert
last_alive = 0

# ---------- TELEGRAM ----------
def send(msg):
    try:
        requests.post(f"{BASE}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=3)
    except:
        pass

# ---------- EXIT ALERT ----------
def on_exit():
    send("🔴 BOT STOPPED / CRASHED")

atexit.register(on_exit)

# ---------- ALERT ----------
def send_alert(pid, price):
    send(
        f"⚡ STOCK ALERT\n"
        f"💰 Price: ₹{price}\n"
        f"🔗 shein://product/{pid}\n"
        f"🔥 TAP FAST"
    )

# ---------- PRODUCT CHECK ----------
def check_product(pid):
    try:
        html = session.get(
            f"https://www.sheinindia.in/p/{pid}", timeout=3
        ).text.lower()

        if "out of stock" in html or "sold out" in html:
            return None

        pm = re.search(r'₹\s*(\d+)', html)
        if not pm:
            return None

        price = int(pm.group(1))
        if price > PRICE_LIMIT:
            return None

        return price

    except:
        return None

# ---------- MAIN ----------
def main():
    global last_alive
    send("🟢 BOT ACTIVE - SHEINVERSE SCANNER")

    while True:
        try:
            html = session.get(COLLECTION_URL, timeout=3).text
            pids = set(re.findall(r'/p/(\d+)', html))

            for pid in pids:
                if pid in seen_products:
                    continue

                price = check_product(pid)
                if price:
                    send_alert(pid, price)
                    seen_products.add(pid)

            # Alive ping every 5 mins
            if time.time() - last_alive > 300:
                send("🟢 BOT ALIVE - SCANNING...")
                last_alive = time.time()

        except:
            time.sleep(1)

        time.sleep(POLL_DELAY)

if __name__ == "__main__":
    main()
