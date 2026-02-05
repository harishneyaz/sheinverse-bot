import requests
import time
import os
import re
from datetime import datetime, timedelta

# ================== ENV ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("BOT_TOKEN or CHAT_ID missing")
    while True:
        time.sleep(60)

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================== URLS ==================
COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
DETAIL_API_URL = "https://www.sheinindia.in/api/goods/get-goods-detail"

# ================== SESSION ==================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.sheinindia.in/"
})

# ================== STATE ==================
# pid -> in_stock(True/False)
stock_state = {}
last_heartbeat = datetime.utcnow()

# ================== TELEGRAM ==================
def tg_text(msg):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def tg_product(title, price, img, pid, restored=False):
    product_url = f"https://www.sheinindia.in/p/{pid}"

    caption = (
        "🚨 MEN SHEINVERSE STOCK 🚨\n\n"
        f"👕 {title[:60]}\n"
        f"💰 ₹{price}\n\n"
        f"{'♻️ RESTOCKED' if restored else '⚡ STOCK LIVE'}"
    )

    requests.post(
        f"{TG}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": caption
        },
        files={
            "photo": requests.get(img, timeout=10).content
        },
        params={
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 OPEN PRODUCT", "url": product_url}
                ]]
            }
        }
    )

# ================== HELPERS ==================
def is_men_product(api_data: dict) -> bool:
    """
    Detect MEN via category data (NOT title).
    """
    text = str(api_data).lower()
    if any(w in text for w in ["women", "girl", "ladies", "kids", "baby"]):
        return False
    return "men" in text

def fetch_product(pid):
    payload = {
        "goods_id": pid,
        "country": "IN",
        "language": "en"
    }

    try:
        r = session.post(DETAIL_API_URL, json=payload, timeout=8).json()
    except:
        return None

    data = r.get("info")
    if not data:
        return None

    # MEN check (category-based)
    if not is_men_product(data):
        return None

    # REAL stock check (SKU-level)
    sku_list = data.get("sku_list", [])
    real_stock = sum(int(s.get("stock_qty", 0)) for s in sku_list)

    if real_stock <= 0:
        return ("OUT", None)

    title = data.get("goods_name", "Men Product")
    price = int(data["salePrice"]["amount"])
    img = data["goods_img"][0].replace("\\/", "/")

    return ("IN", title, price, img)

# ================== START ==================
tg_text("🚀 SHEINVERSE MEN STOCK BOT STARTED")
print("BOT RUNNING")

# ================== LOOP ==================
while True:
    try:
        # Heartbeat every 1 hour
        if datetime.utcnow() - last_heartbeat >= timedelta(hours=1):
            tg_text("✅ BOT RUNNING — monitoring MEN SHEINVERSE stock")
            last_heartbeat = datetime.utcnow()

        html = session.get(COLLECTION_URL, timeout=10).text
        pids = set(re.findall(r'"goods_id":"(\d+)"', html))

        for pid in pids:
            result = fetch_product(pid)

            if not result:
                continue

            prev_state = stock_state.get(pid, False)

            if result[0] == "OUT":
                stock_state[pid] = False
                continue

            _, title, price, img = result

            if not prev_state:
                # NEW STOCK or RESTOCK
                tg_product(
                    title=title,
                    price=price,
                    img=img,
                    pid=pid,
                    restored=(pid in stock_state)
                )

            stock_state[pid] = True

        print("scan done")
        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
