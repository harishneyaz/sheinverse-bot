import requests
import time
import os
import re
import json

# ================== ENV ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ BOT_TOKEN or CHAT_ID missing")
    while True:
        time.sleep(60)

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================== URLS ==================
COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
DETAIL_API_URL = "https://www.sheinindia.in/api/goods/get-goods-detail"

# ================== SESSION ==================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.sheinindia.in/"
}

session = requests.Session()
session.headers.update(HEADERS)

# ================== STATE ==================
stock_state = {}        # pid -> True / False
last_heartbeat = 0      # hourly heartbeat

# ================== TELEGRAM ==================
def tg_text(msg):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def tg_product(title, price, img, pid):
    product_url = f"https://www.sheinindia.in/p/{pid}"

    requests.post(
        f"{TG}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": (
                "🚨 MEN SHEINVERSE RESTOCK 🚨\n\n"
                f"👕 {title[:60]}\n"
                f"💰 ₹{price}\n\n"
                f"🔗 {product_url}"
            ),
            "reply_markup": json.dumps({
                "inline_keyboard": [[
                    {"text": "🛒 OPEN PRODUCT", "url": product_url}
                ]]
            })
        },
        files={
            "photo": requests.get(img, timeout=10).content
        }
    )

# ================== DATA ==================
def get_product_ids():
    try:
        html = session.get(COLLECTION_URL, timeout=10).text
        return set(re.findall(r'"goods_id":"(\d+)"', html))
    except:
        return set()

def fetch_product(pid):
    payload = {"goods_id": pid, "country": "IN", "language": "en"}

    try:
        r = session.post(DETAIL_API_URL, json=payload, timeout=8).json()
    except:
        return None

    data = r.get("info")
    if not data:
        return None

    title_lower = data.get("goods_name", "").lower()

    # MEN ONLY (hard filter)
    if not any(x in title_lower for x in ["men", "mens", "man's"]):
        return None
    if any(x in title_lower for x in ["women", "kids", "girl", "boy"]):
        return None

    # REAL BUYABLE STOCK ONLY
    for sku in data.get("sku_list", []):
        if sku.get("is_enable") == 1 and int(sku.get("stock_qty", 0)) > 0:
            price = int(data["salePrice"]["amount"])
            img = data["goods_img"][0].replace("\\/", "/")
            return data["goods_name"], price, img

    return None

# ================== START ==================
tg_text("🚀 SHEINVERSE MEN STOCK BOT STARTED")
print("BOT RUNNING")

while True:
    try:
        pids = get_product_ids()

        for pid in pids:
            product = fetch_product(pid)

            prev = stock_state.get(pid, False)
            curr = bool(product)

            # ALERT ONLY ON OUT -> IN
            if curr and not prev:
                title, price, img = product
                tg_product(title, price, img, pid)

            stock_state[pid] = curr

        # HEARTBEAT (every 1 hour)
        if time.time() - last_heartbeat > 3600:
            tg_text("🟢 SHEIN BOT RUNNING")
            last_heartbeat = time.time()

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
