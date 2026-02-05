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
stock_state = {}  # pid -> {in_stock, title, price, img, men, women, total_stock}
last_heartbeat = datetime.utcnow()
last_summary = datetime.utcnow() - timedelta(hours=2)

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
        "🚨 MEN SHEINVERSE STOCK ALERT 🚨\n\n"
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
    men_lines = []
    women_lines = []
    men_count = 0
    women_count = 0
    for pid, info in stock_state.items():
        if info.get("total_stock", 0) > 0:
            line = f"👕 {info['title'][:50]} | ₹{info['price']} | Stock: {info['total_stock']}\nhttps://www.sheinindia.in/p/{pid}"
            if info.get("men"):
                men_lines.append(line)
                men_count += 1
            else:
                women_lines.append(line)
                women_count += 1

    msg = f"📊 CURRENT AVAILABLE STOCK:\n\n🧑 MEN ({men_count} items):\n"
    msg += "\n\n".join(men_lines) if men_lines else "None"
    msg += f"\n\n👩 WOMEN/OTHER ({women_count} items):\n"
    msg += "\n\n".join(women_lines) if women_lines else "None"

    tg_text(msg)

# ================== HELPERS ==================
def fetch_product(pid):
    payload = {"goods_id": pid, "country": "IN", "language": "en"}
    try:
        r = session.post(DETAIL_API_URL, json=payload, timeout=8).json()
    except:
        return None

    data = r.get("info")
    if not data:
        return None

    sku_list = data.get("sku_list", [])
    # Total stock for summary (ignore is_enable)
    total_stock = sum(int(s.get("stock_qty", 0)) for s in sku_list)
    # Buyable stock for Men alert
    alert_stock = sum(int(s.get("stock_qty", 0)) for s in sku_list if s.get("is_enable") == 1)

    if total_stock <= 0:
        return ("OUT",)

    title = data.get("goods_name", "Product")
    price = int(data["salePrice"]["amount"])
    img = data["goods_img"][0].replace("\\/", "/")

    text = str(data).lower()
    men_check = "men" in text and not any(w in text for w in ["women", "girl", "ladies", "kids", "baby"])
    women_check = not men_check

    return ("IN", title, price, img, men_check, women_check, total_stock, alert_stock)

# ================== START ==================
tg_text("🚀 SHEINVERSE BOT STARTED — scanning current stock")
print("BOT RUNNING")

# Show current stock immediately
html = session.get(COLLECTION_URL, timeout=10).text
pids = set(re.findall(r'"goods_id":"(\d+)"', html))
for pid in pids:
    result = fetch_product(pid)
    if result and result[0] == "IN":
        _, title, price, img, men_check, women_check, total_stock, alert_stock = result
        stock_state[pid] = {
            "in_stock": alert_stock > 0,
            "title": title,
            "price": price,
            "img": img,
            "men": men_check,
            "women": women_check,
            "total_stock": total_stock
        }
tg_summary()

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
                stock_state[pid] = {"in_stock": False, "total_stock": 0}
                continue

            _, title, price, img, men_check, women_check, total_stock, alert_stock = result

            # Send Men alerts if buyable stock exists and previously out of stock
            if men_check and alert_stock > 0 and not prev_state.get("in_stock", False):
                tg_product(
                    title=title,
                    price=price,
                    img=img,
                    pid=pid,
                    restored=(pid in stock_state)
                )

            # Update state for summary
            stock_state[pid] = {
                "in_stock": alert_stock > 0,
                "title": title,
                "price": price,
                "img": img,
                "men": men_check,
                "women": women_check,
                "total_stock": total_stock
            }

        print("scan done")
        time.sleep(0.5)  # faster polling to catch flash stock

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
