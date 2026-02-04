import requests, time, re, os, atexit

# ===== ENV CONFIG =====
TOKEN = os.getenv("TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
BASE = f"https://api.telegram.org/bot{TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
PRICE_LIMIT = 1020
POLL_DELAY = 1  # ultra-fast

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
})

seen_products = {}   # pid -> last_price
last_alive = 0

# ---------- TELEGRAM ----------
def send(msg):
    try:
        requests.post(f"{BASE}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=5)
    except:
        pass

# ---------- EXIT ALERT ----------
def on_exit():
    send("🔴 VIRUS SO GAYA\n⛔ Bot stopped / crashed")

atexit.register(on_exit)

# ---------- ALERT ----------
def send_alert(pid, price, category):
    send(
        "⚡ FIRST STOCK ALERT\n"
        f"👕 Category: {category}\n"
        f"💰 Price: ₹{price}\n"
        f"🔗 shein://product/{pid}\n"
        "🔥 FAST BUY"
    )

# ---------- PRODUCT CHECK ----------
def check_product(pid):
    try:
        html = session.get(
            f"https://www.sheinindia.in/p/{pid}",
            timeout=6
        ).text.lower()

        if "out of stock" in html or "sold out" in html:
            return None

        pm = re.search(r'₹\s*(\d+)', html)
        if not pm:
            return None

        price = int(pm.group(1))
        if price > PRICE_LIMIT:
            return None

        # Categories
        is_tshirt = any(x in html for x in ["t-shirt", "tshirt"])
        is_shirt = "shirt" in html and not is_tshirt
        is_hoodie = "hoodie" in html
        is_jeans = "jeans" in html
        is_pants = any(x in html for x in ["pants", "trouser"])

        # Topwear sizes
        if is_tshirt or is_shirt or is_hoodie:
            if '"m"' in html or '"l"' in html:
                return price, "Topwear"

        # Bottomwear sizes
        if is_jeans or is_pants:
            if '"30"' in html or '"32"' in html:
                return price, "Bottomwear"

        return None

    except:
        return None

# ---------- MAIN ----------
def main():
    global last_alive
    send("🟢 VIRUS ZINDA HAI\nShein pr nazar hai")

    while True:
        try:
            html = session.get(COLLECTION_URL, timeout=6).text
            pids = set(re.findall(r'/p/(\d+)', html))

            for pid in pids:
                result = check_product(pid)
                if not result:
                    continue

                price, category = result

                if pid not in seen_products or price < seen_products[pid]:
                    send_alert(pid, price, category)
                    seen_products[pid] = price

            # Alive ping every 5 minutes
            if time.time() - last_alive > 300:
                send("🟢 VIRUS ALIVE\nScanning…")
                last_alive = time.time()

        except:
            send("⚠️ ERROR\nRetrying…")
            time.sleep(5)

        time.sleep(POLL_DELAY if not seen_products else 2)

# ---------- RUN ----------
if __name__ == "__main__":
    main()
