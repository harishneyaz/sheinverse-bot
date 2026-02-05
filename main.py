import requests, time, re, os, sys

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
DELAY = 1.0   # max safe speed

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android)",
    "Accept-Language": "en-IN,en;q=0.9"
})

seen = set()

def tg_text(msg):
    requests.post(f"{BASE}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg,
        "disable_notification": False
    })

def tg_product(pid, price, img, title):
    product = f"https://www.sheinindia.in/p/{pid}"

    r = requests.post(
        f"{BASE}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": (
                "🚨 MEN SHEINVERSE STOCK 🚨\n\n"
                f"👕 {title[:60]}\n"
                f"💰 ₹{price}\n\n"
                "⚡ CLICK FAST"
            ),
            "disable_notification": False
        },
        files={"photo": requests.get(img).content},
        params={
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 OPEN PRODUCT", "url": product}
                ]]
            }
        }
    ).json()

    if "result" in r:
        requests.post(f"{BASE}/pinChatMessage", data={
            "chat_id": CHAT_ID,
            "message_id": r["result"]["message_id"]
        })

tg_text("🚀 MEN SHEINVERSE BOT STARTED\n🔔 Alerts ON")

def is_men_product(html):
    # ❌ HARD reject women/kids
    if any(w in html for w in [
        "women", "ladies", "girl", "crop", "skirt",
        "bra", "dress", "kids", "baby"
    ]):
        return False

    # ✅ Men clothing keywords (app style)
    return any(w in html for w in [
        "men", "t-shirt", "tshirt", "shirt",
        "hoodie", "sweatshirt",
        "jeans", "pants", "trouser",
        "jacket", "track pant"
    ])

def check_product(pid):
    url = f"https://www.sheinindia.in/p/{pid}"
    html = session.get(url, timeout=8).text.lower()

    if not is_men_product(html):
        return None

    price_m = re.search(r'"(saleprice|finalprice|price)":\s*"?(\d+)"?', html)
    img_m = re.search(r'"coverimage":"(https:[^"]+)"', html)
    title_m = re.search(r'"goods_name":"([^"]+)"', html)

    if not price_m or not img_m:
        return None

    return (
        int(price_m.group(2)),
        img_m.group(1),
        title_m.group(1) if title_m else "Men Clothing"
    )

try:
    while True:
        html = session.get(COLLECTION_URL, timeout=8).text
        pids = set(re.findall(r'"goods_id":"(\d+)"', html))

        for pid in pids:
            if pid in seen:
                continue

            data = check_product(pid)
            if data:
                price, img, title = data
                tg_product(pid, price, img, title)
                seen.add(pid)

        time.sleep(DELAY)

except Exception as e:
    tg_text(f"❌ BOT STOPPED\n{e}")
    sys.exit(1)
