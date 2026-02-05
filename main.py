import requests, time, os, re

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ BOT_TOKEN or CHAT_ID missing")
    while True:
        time.sleep(60)

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
API_URL = "https://www.sheinindia.in/api/goods/get-goods-detail"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.sheinindia.in/"
}

session = requests.Session()
session.headers.update(HEADERS)

seen = set()

def tg_text(msg):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def tg_product(title, price, img, pid):
    product = f"https://www.sheinindia.in/p/{pid}"

    requests.post(
        f"{TG}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": (
                "🚨 MEN SHEINVERSE STOCK 🚨\n\n"
                f"👕 {title[:60]}\n"
                f"💰 ₹{price}\n\n"
                "⚡ STOCK LIVE"
            )
        },
        files={"photo": requests.get(img, timeout=10).content},
        params={
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 OPEN PRODUCT", "url": product}
                ]]
            }
        }
    )

def fetch_product(pid):
    payload = {"goods_id": pid, "country": "IN", "language": "en"}

    try:
        r = session.post(API_URL, json=payload, timeout=8).json()
    except:
        return None

    data = r.get("info")
    if not data:
        return None

    title = data.get("goods_name", "")
    if not any(x in title.lower() for x in ["men", "mens", "man's"]):
        return None

    sku_list = data.get("sku_list", [])
    stock = sum(int(s.get("stock_qty", 0)) for s in sku_list)

    if stock <= 0:
        return None

    price = int(data["salePrice"]["amount"])
    img = data["goods_img"][0].replace("\\/", "/")

    return title, price, img

tg_text("🚀 SHEIN API BOT STARTED")
print("BOT RUNNING")

while True:
    try:
        html = session.get(COLLECTION_URL, timeout=10).text
        pids = set(re.findall(r'"goods_id":"(\d+)"', html))

        for pid in pids:
            if pid in seen:
                continue

            product = fetch_product(pid)
            if product:
                title, price, img = product
                tg_product(title, price, img, pid)
                seen.add(pid)

        print("scan done")
        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
