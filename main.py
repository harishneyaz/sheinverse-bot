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
last_summary = datetime.utcnow() - timedelta(hours=2)  # force first summary

# ================== TELEGRAM ==================
def tg_text(msg):
    try:
        requests.post(f"{TG}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=10)
    except:
        pass

def tg_product(title, price, img, pid, restored=False):
    product_url = f"https://www.sheinindia.in/p/{pid}"
    caption = (
        "🚨 MEN SHEINVERSE STOCK 🚨\n\n"
        f"👕 {title[:60]}\n"
        f"💰 ₹{price}\n\n"
        f"{'♻️ RESTOCKED' if restored else '⚡ STOCK LIVE'}"
    )
    try:
        requests.post(
            f"{TG}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"photo": requests.get(img, timeout=10).content},
            params={
                "reply_markup": {"inline_keyboard": [[{"text": "🛒 OPEN PRODUCT", "url": product_url}]]}
            },
            timeout=15
        )
    except:
        pass

def tg_summary():
    """Send a summary of all available stock (Men/Women)."""
    summary_lines = []
    for pid, info in stock_state.items():
        if info.get("in_stock"):
            line = f"👕 {info['title'][:50]} | ₹{info['price']}\nhttps://www.sheinindia.in/p/{pid}"
            summary_lines.append(line)
    if summary_lines:
        msg = "📊 CURRENT AVAILABLE STOCK:\n\n" + "\n\n".join(summary_lines)
        tg_text(msg)
    else:
        tg_text("📊 CURRENT AVAILABLE STOCK: None")

# ================== HELPERS ==================
def is_men_product(api_data: dict) -> bool:
    text = str(api_data).lower()
    if any(w in text for w in ["women", "girl", "ladies", "kids", "baby"]):
        return False
    return "men" in text

def fetch_product(pid):
    payload = {"goods_id": pid, "country": "IN", "language": "en"}
    try:
        r = session.post(DETAIL_API_URL, json=payload, timeout=8).json()
    except:
        return None

    data = r.get("info")
    if not data:
        return None

    # MEN filter
    men_check = is_men_product(data)
    # SKU-level real stock
    sku_list = data.get("sku_list", [])
    in_stock = False
    for s in sku_list:
        if s.get("is_enable") == 1 and int(s.get("stock_qty", 0)) > 0:
            in_stock = True
            break

    if not in_stock:
        return ("OUT",)

    title = data.get("goods_name", "Product")
    price = int(data["salePrice"]["amount"])
    img = data["goods_img"][0].replace("\\/", "/")

    return ("IN", title, price, img, men_check)

# ================== START ==================
tg_text("🚀 SHEINVERSE BOT STARTED — scanning current stock")
print("BOT RUNNING")

# ================== LOOP ==================
while True:
    try:
        # Heartbeat every 1 hour
        if datetime.utcnow() - last_heartbeat >= timedelta(hours=1):
            tg_text("✅ BOT RUNNING — monitoring SHEINVERSE stock")
            last_heartbeat = datetime.utcnow()

        # Summary every 2 hours
        if datetime.utcnow() - last_summary >= timedelta(hours=2):
            tg_summary()
            last_summary = datetime.utcnow()

        html = session.get(COLLECTION_URL, timeout=10).text
        pids = set(re.findall(r'"goods_id":"(\d+)"', html))

        for pid in pids:
            result = fetch_product(pid)
            if not result:
                continue

            prev_state = stock_state.get(pid, {"in_stock": False})
            if result[0] == "OUT":
                stock_state[pid] = {"in_stock": False}
                continue

            _, title, price, img, men_check = result

            # If not previously in stock → send alert
            if not prev_state["in_stock"]:
                tg_product(
                    title=title,
                    price=price,
                    img=img,
                    pid=pid,
                    restored=(pid in stock_state)
                )

            stock_state[pid] = {
                "in_stock": True,
                "title": title,
                "price": price,
                "img": img,
                "men": men_check
            }

        print("scan done")
        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
