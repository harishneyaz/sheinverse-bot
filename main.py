import requests, time, re, os, sys

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

API_URL = "https://www.sheinindia.in/api/collection/get_goods"
COLLECTION_ID = "SHEINVERSE"
PRICE_LIMIT = 1020
DELAY = 1.0   # 🔥 MAX SPEED (FREE SAFE)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
})

seen = set()

def send(msg):
    requests.post(f"{BASE}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": msg})

def send_product(pid, price):
    product = f"https://www.sheinindia.in/p/{pid}"
    cart = f"shein://cart/add?goods_id={pid}"

    requests.post(
        f"{BASE}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": (
                "⚡ ULTRA FAST MEN ALERT\n"
                f"🆔 {pid}\n"
                f"💰 ₹{price}\n\n"
                "🚀 BUY FAST"
            ),
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 ADD TO CART", "url": cart},
                    {"text": "🔗 PRODUCT", "url": product}
                ]]
            }
        }
    )

send("🚀 ULTRA FAST MODE ENABLED")

def check(pid):
    html = session.get(
        f"https://www.sheinindia.in/p/{pid}",
        timeout=8
    ).text.lower()

    # MEN only
    if any(x in html for x in ["women", "ladies", "girl", "kids"]):
        return None
    if not any(x in html for x in ["men", "male", "man"]):
        return None

    # category
    if not any(x in html for x in [
        "t-shirt", "tshirt", "shirt",
        "hoodie", "sweatshirt",
        "jeans", "pants", "trouser"
    ]):
        return None

    pm = re.search(r'"saleprice":(\d+)', html)
    if not pm:
        return None

    price = int(pm.group(1))
    if price > PRICE_LIMIT:
        return None

    return price

try:
    page = 1
    while True:
        payload = {
            "collection_id": COLLECTION_ID,
            "page": page,
            "page_size": 50
        }

        r = session.post(API_URL, json=payload, timeout=8).json()
        goods = r.get("goods_list", [])

        for g in goods:
            pid = str(g.get("goods_id"))
            if pid in seen:
                continue

            price = g.get("sale_price")
            if price and price <= PRICE_LIMIT:
                result = check(pid)
                if result:
                    send_product(pid, price)
                    seen.add(pid)

        page = page + 1 if page < 3 else 1
        time.sleep(DELAY)

except Exception as e:
    send(f"❌ BOT STOPPED\n{e}")
    sys.exit(1)
