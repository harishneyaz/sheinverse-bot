import requests, time, os, json, re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("❌ BOT_TOKEN / CHAT_ID missing")

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/sheinverse"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13)",
    "Accept": "text/html"
}

STATE_FILE = "state.json"


def tg_msg(text):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })


def tg_photo(img, caption):
    requests.post(f"{TG}/sendPhoto", json={
        "chat_id": CHAT_ID,
        "photo": img,
        "caption": caption,
        "parse_mode": "HTML"
    })


def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {}


def save_state(data):
    json.dump(data, open(STATE_FILE, "w"))


tg_msg("🤖 <b>SheinVerse MEN Bot Started</b>\nMonitoring LIVE stock…")

state = load_state()
last_heartbeat = time.time()

while True:
    try:
        html = requests.get(COLLECTION_URL, headers=HEADERS, timeout=15).text

        # 🔍 Extract embedded JSON product blocks
        products = re.findall(r'"goods_id":"(\d+)".*?"stock":"(\d+)".*?"goods_name":"(.*?)".*?"goods_img":"(.*?)"', html)

        men_total = 0

        for pid, stock, name, img in products:
            stock = int(stock)
            men_total += stock

            old_stock = state.get(pid, 0)

            if stock > 0 and old_stock == 0:
                link = f"https://www.sheinindia.in/p/{pid}"

                tg_photo(
                    img.replace("\\/", "/"),
                    f"🔥 <b>MEN STOCK ALERT</b>\n\n"
                    f"👕 {name}\n"
                    f"📦 Stock: {stock}\n"
                    f"🛒 <a href='{link}'>BUY NOW</a>"
                )

            state[pid] = stock

        save_state(state)

        # ❤️ Heartbeat every 2 hours
        if time.time() - last_heartbeat > 7200:
            tg_msg(
                f"💓 <b>Bot Alive</b>\n\n"
                f"👔 MEN Current Stock: {men_total}"
            )
            last_heartbeat = time.time()

        time.sleep(15)

    except Exception as e:
        tg_msg(f"⚠️ Error: {e}")
        time.sleep(30)
