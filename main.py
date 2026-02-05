import requests, time, os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
API_URL = "https://www.sheinindia.in/api/goods/get-goods-detail"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

seen = set()
session = requests.Session()
session.headers.update(HEADERS)

def tg_text(msg):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def tg_product(title, price, img, pid):
    product = f"https://www.sheinindia.in/p/{pid}"

    r = requests.post(
        f"{TG}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption":
                f"🚨 MEN SHEINVERSE STOCK 🚨\n\n"
                f"👕 {title[:60]}\n"
                f"💰 ₹{price}\n\n"
                f"⚡ STOCK LIVE",
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

def fetch_product(pid):
    payload = {
        "goods_id": pid
    }

    r = session.post(API_URL, json=payload, timeout=6).json()

    data = r.get("info")
    if not data:
        return None

    # MEN check
    if "men" not in str(data).lower():
        return None

    stock = data.get("stock", 0)
    if stock <= 0:
        return None

    price = int(data["salePrice"]["amount"])
    title = data["goods_name"]
    img = data["goods_img"][0]

    return title, price, img

tg_text("🚀 SHEIN API STOCK BOT STARTED")

while True:
    html = session.get(COLLECTION_URL).text
    pids = set(pid for pid in html.split('"goods_id":"')[1:])

    for p in pids:
        pid = p.split('"')[0]

        if pid in seen:
            continue

        product = fetch_product(pid)
        if product:
            title, price, img = product
            tg_product(title, price, img, pid)
            seen.add(pid)

    time.sleep(0.8)
