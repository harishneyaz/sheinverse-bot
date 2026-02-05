import requests, time, os, random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("BOT_TOKEN or CHAT_ID missing")
    while True:
        time.sleep(60)

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

LIST_API = "https://www.sheinindia.in/api/collection/get-products"
DETAIL_API = "https://www.sheinindia.in/api/goods/get-goods-detail"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

session = requests.Session()
session.headers.update(HEADERS)

stock_cache = {}

def tg_text(msg):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def tg_product(title, price, img, pid, stock):
    requests.post(
        f"{TG}/sendPhoto",
        json={
            "chat_id": CHAT_ID,
            "photo": img,
            "caption": (
                "🚨 MEN SHEINVERSE RESTOCK 🚨\n\n"
                f"👕 {title[:60]}\n"
                f"📦 Stock: {stock}\n"
                f"💰 ₹{price}"
            ),
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 BUY NOW", "url": f"https://www.sheinindia.in/p/{pid}"}
                ]]
            }
        }
    )

def fetch_detail(pid):
    r = session.post(DETAIL_API, json={
        "goods_id": pid,
        "country": "IN",
        "language": "en"
    }).json()

    info = r.get("info")
    if not info:
        return None

    title = info["goods_name"]
    title_l = title.lower()

    stock = sum(int(s["stock_qty"]) for s in info["sku_list"])
    price = int(info["salePrice"]["amount"])
    img = info["goods_img"][0].replace("\\/", "/")

    return title, title_l, stock, price, img

tg_text("🚀 SHEINVERSE PRO BOT STARTED")

while True:
    try:
        r = session.post(LIST_API, json={
            "collection_id": "5939",
            "sub_collection_id": "37961",
            "page": 1,
            "page_size": 100,
            "country": "IN"
        }).json()

        goods = r.get("info", {}).get("goods", [])

        men_total = 0
        women_total = 0

        for g in goods:
            pid = g["goods_id"]
            detail = fetch_detail(pid)
            if not detail:
                continue

            title, title_l, stock, price, img = detail
            last = stock_cache.get(pid, 0)

            is_men = "men" in title_l

            if stock > 0:
                if is_men:
                    men_total += stock
                else:
                    women_total += stock

            # 🔥 MEN RESTOCK ALERT
            if is_men and stock > 0 and last == 0:
                tg_product(title, price, img, pid, stock)

            stock_cache[pid] = stock

        tg_text(
            "📊 SHEINVERSE LIVE SUMMARY\n\n"
            f"👔 Men stock: {men_total}\n"
            f"👗 Women stock: {women_total}"
        )

        time.sleep(random.uniform(6, 9))

    except Exception as e:
        print("ERROR:", e)
        time.sleep(10)
