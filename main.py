import requests, time, os, re, random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ BOT_TOKEN or CHAT_ID missing")
    while True:
        time.sleep(60)

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ✅ REAL SHEIN VERSE URL (PUBLIC)
COLLECTION_URL = "https://sheinindia.in/sheinverse/c/sverse-5939-37961"
API_URL = "https://www.sheinindia.in/api/goods/get-goods-detail"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android 13)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.sheinindia.in/"
}

session = requests.Session()
session.headers.update(HEADERS)

# pid -> last stock
stock_cache = {}

def tg_text(msg):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def tg_product(title, price, img, pid, stock):
    product = f"https://www.sheinindia.in/p/{pid}"

    requests.post(
        f"{TG}/sendPhoto",
        json={
            "chat_id": CHAT_ID,
            "photo": img,
            "caption": (
                "🚨 MEN SHEINVERSE STOCK 🚨\n\n"
                f"👕 {title[:60]}\n"
                f"📦 Stock: {stock}\n"
                f"💰 ₹{price}\n\n"
                "⚡ JUST DROPPED / RESTOCKED"
            ),
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 BUY FAST", "url": product}
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
    title_l = title.lower()

    sku_list = data.get("sku_list", [])
    stock = sum(int(s.get("stock_qty", 0)) for s in sku_list)

    price = int(data["salePrice"]["amount"])
    img = data["goods_img"][0].replace("\\/", "/")

    return title, title_l, price, img, stock

# 🔔 BOT START MESSAGE
tg_text("🚀 SHEINVERSE PRO BOT STARTED\n⚡ Fast • Accurate • MEN Focused")
print("BOT RUNNING")

while True:
    try:
        html = session.get(COLLECTION_URL, timeout=10).text
        pids = set(re.findall(r'"goods_id":"(\d+)"', html))

        men_total = 0
        women_total = 0

        for pid in pids:
            data = fetch_product(pid)
            if not data:
                continue

            title, title_l, price, img, stock = data
            last_stock = stock_cache.get(pid, 0)

            is_men = any(k in title_l for k in ["men", "mens", "man's"])

            if stock > 0:
                if is_men:
                    men_total += stock
                else:
                    women_total += stock

            # 🔥 NEW STOCK OR RESTOCK (MEN ONLY)
            if is_men and stock > 0 and last_stock == 0:
                tg_product(title, price, img, pid, stock)

            stock_cache[pid] = stock

        # 📊 SUMMARY (ALWAYS CORRECT)
        tg_text(
            "📊 SHEINVERSE LIVE SUMMARY\n\n"
            f"👔 Men stock: {men_total}\n"
            f"👗 Women stock: {women_total}"
        )

        # ⚡ SAFE FAST CHECK (ANTI-BAN)
        time.sleep(random.uniform(6, 9))

    except Exception as e:
        print("ERROR:", e)
        time.sleep(10)
