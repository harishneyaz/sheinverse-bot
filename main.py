import requests, time, re, os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
PRICE_LIMIT = 1020
DELAY = 3

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
})

seen = set()

def send(msg):
    requests.post(
        f"{BASE}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

send("🚀 SHEINVERSE BOT STARTED")

def extract_products(html):
    return set(re.findall(r'"goods_id":"(\d+)"', html))

def check(pid):
    url = f"https://www.sheinindia.in/p/{pid}"
    html = session.get(url, timeout=10).text

    # PRICE (JSON)
    pm = re.search(r'"salePrice":(\d+)', html)
    if not pm:
        return False

    price = int(pm.group(1))
    if price > PRICE_LIMIT:
        return False

    # SIZE
    if any(s in html for s in ['"30"','"32"','"m"','"l"']):
        return price

    return False

while True:
    try:
        html = session.get(COLLECTION_URL, timeout=10).text
        pids = extract_products(html)

        for pid in pids - seen:
            price = check(pid)
            if price:
                send(f"⚡ SHEINVERSE ALERT\n🆔 {pid}\n💰 ₹{price}\n🔥 BUY FAST")
                seen.add(pid)

    except Exception as e:
        send(f"⚠️ ERROR: {e}")

    time.sleep(DELAY)
