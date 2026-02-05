import requests, time, re, os, sys

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

COLLECTION_URL = "https://www.sheinindia.in/collection/SHEINVERSE"
PRICE_LIMIT = 1020
DELAY = 1.8

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

seen = set()

def send(msg):
    requests.post(f"{BASE}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg})

def send_product(pid, price, img):
    product = f"https://www.sheinindia.in/p/{pid}"
    cart = f"shein://cart/add?goods_id={pid}"

    requests.post(
        f"{BASE}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": (
                "⚡ MEN SHEINVERSE ALERT\n"
                f"🆔 {pid}\n"
                f"💰 ₹{price}\n\n"
                "🚀 BUY FAST"
            )
        },
        files={"photo": requests.get(img).content},
        params={
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 ADD TO CART", "url": cart},
                    {"text": "🔗 PRODUCT", "url": product}
                ]]
            }
        }
    )

send("🚀 MEN SHEINVERSE BOT STARTED")

def check(pid):
    html = session.get(
        f"https://www.sheinindia.in/p/{pid}",
        timeout=10
    ).text.lower()

    # ❌ reject women/kids
    if any(x in html for x in [
        "women", "girl", "ladies", "kids", "baby"
    ]):
        return None

    # ✅ men check
    if not any(x in html for x in [
        "men", "male", "man"
    ]):
        return None

    # category
    if not any(x in html for x in [
        "t-shirt", "tshirt", "shirt",
        "hoodie", "sweatshirt",
        "jeans", "pants", "trouser"
    ]):
        return None

    pm = re.search(r'"saleprice":(\d+)', html)
    if not pm:
        return None

    price = int(pm.group(1))
    if price > PRICE_LIMIT:
        return None

    im = re.search(r'"coverimage":"(https:[^"]+)"', html)
    img = im.group(1) if im else None

    return price, img

try:
    while True:
        html = session.get(COLLECTION_URL, timeout=10).text
        pids = set(re.findall(r'"goods_id":"(\d+)"', html))

        for pid in pids - seen:
            result = check(pid)
            if result:
                price, img = result
                send_product(pid, price, img)
                seen.add(pid)

        time.sleep(DELAY)

except Exception as e:
    send(f"❌ BOT STOPPED\n{e}")
    sys.exit(1)
