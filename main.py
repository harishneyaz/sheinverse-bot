import os
import time
import re
import requests

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ BOT_TOKEN or CHAT_ID missing")
    while True:
        time.sleep(60)

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# SHEINVERSE URLs (Chrome-openable)
MEN_URL = "https://sheinindia.in/sheinverse/c/sverse-5939-37961"
WOMEN_URL = "https://sheinindia.in/sheinverse/c/sverse-5939-37960"

CHECK_INTERVAL = 1            # 1 second
SUMMARY_INTERVAL = 2 * 60 * 60  # 2 hours

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13)",
    "Accept": "text/html"
}

session = requests.Session()
session.headers.update(HEADERS)

seen_instock = set()
last_summary = 0
# =========================================

def tg_text(text):
    requests.post(f"{TG_API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": text
    })

def tg_photo(img, caption, link):
    requests.post(
        f"{TG_API}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": caption,
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 BUY NOW", "url": link}
                ]]
            }
        },
        files={"photo": requests.get(img, timeout=10).content}
    )

def extract_products(html):
    """
    Website-based parsing (stable)
    """
    products = []
    blocks = re.findall(r'"goods_id":"(\d+)".*?"goods_name":"(.*?)".*?"goods_img":"(.*?)".*?"salePrice":\{"amount":(\d+)\}', html)
    for pid, name, img, price in blocks:
        products.append({
            "id": pid,
            "name": name.replace("\\u002F", "/"),
            "img": "https:" + img.replace("\\/", "/"),
            "price": price
        })
    return products

def fetch_page(url):
    try:
        return session.get(url, timeout=10).text
    except:
        return ""

# ================= START ==================
tg_text("🤖 SHEIN Verse Bot Started\n⚡ MEN restock alerts ON\n📊 Summary every 2 hours")
print("BOT RUNNING")

while True:
    try:
        men_html = fetch_page(MEN_URL)
        women_html = fetch_page(WOMEN_URL)

        men_products = extract_products(men_html)
        women_products = extract_products(women_html)

        men_count = len(men_products)
        women_count = len(women_products)

        # MEN alerts (new / restock)
        for p in men_products:
            if p["id"] not in seen_instock:
                seen_instock.add(p["id"])

                caption = (
                    "🚨 MEN SHEINVERSE STOCK 🚨\n\n"
                    f"👕 {p['name'][:60]}\n"
                    f"💰 ₹{p['price']}\n\n"
                    "⚡ STOCK LIVE"
                )
                link = f"https://sheinindia.in/p/{p['id']}"
                tg_photo(p["img"], caption, link)

        # Summary (start + every 2 hours)
        if time.time() - last_summary > SUMMARY_INTERVAL:
            tg_text(
                f"📊 Current Stock Summary\n"
                f"👔 Men: {men_count}\n"
                f"👗 Women: {women_count}"
            )
            last_summary = time.time()

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
