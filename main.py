import asyncio
import aiohttp
import random
import os
import sys
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

print("🚀 Container booting...")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ ENV missing")
    sys.exit(1)

print("✅ ENV loaded")

MEN_CAT_ID = "37961"
WOMEN_CAT_ID = "37960"

CHECK_MIN = 18
CHECK_MAX = 35

API_URL = "https://api-service.shein.com/v1/goods/list"

HEADERS = {
    "user-agent": "Mozilla/5.0",
    "accept": "application/json"
}

bot = Bot(token=TELEGRAM_TOKEN)
LAST_STATE = {}

# ================== STOCK CHECK HELPER ==================
def is_in_stock(p):
    if p.get("goods_stock", 0) > 0:
        return True
    if p.get("stock_status") == 1:
        return True
    if p.get("sale_status") == 1:
        return True
    return False

# ================== FETCH ==================
async def fetch_products(cat_id):
    params = {
        "cat_id": cat_id,
        "page": 1,
        "page_size": 80,
        "country": "IN",
        "language": "en",
        "currency": "INR"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, headers=HEADERS, params=params, timeout=20) as r:
            data = await r.json()
            return data.get("goods_list", [])

# ================== ALERT ==================
async def send_alert(p, title):
    link = f"https://sheinindia.in/{p.get('goods_url','')}"
    await bot.send_photo(
        chat_id=CHAT_ID,
        photo=p.get("goods_img"),
        caption=f"""{title}

👕 {p.get('goods_name')}
💰 ₹{p.get('sale_price')}
🔗 Buy:
{link}

⚡ FAST BUY
"""
    )

# ================== MEN CHECK ==================
async def check_men_stock():
    products = await fetch_products(MEN_CAT_ID)

    for p in products:
        pid = p["goods_id"]
        in_stock = is_in_stock(p)

        if pid not in LAST_STATE:
            LAST_STATE[pid] = in_stock
            if in_stock:
                await send_alert(p, "🆕 NEW MEN STOCK")
        else:
            if LAST_STATE[pid] is False and in_stock is True:
                LAST_STATE[pid] = True
                await send_alert(p, "🔁 MEN RESTOCK")

# ================== SUMMARY ==================
async def send_summary():
    men = await fetch_products(MEN_CAT_ID)
    women = await fetch_products(WOMEN_CAT_ID)

    men_count = sum(1 for p in men if is_in_stock(p))
    women_count = sum(1 for p in women if is_in_stock(p))

    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"""📊 SHEIN VERSE LIVE STATUS

👨 Men in stock: {men_count}
👩 Women in stock: {women_count}

✅ Data verified from API
"""
    )

# ================== MAIN ==================
async def main():
    print("🤖 Bot starting...")

    await bot.send_message(
        chat_id=CHAT_ID,
        text="🤖 SHEIN VERSE BOT STARTED\nFetching live stock…"
    )

    await send_summary()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_summary, "interval", hours=2)
    scheduler.start()

    while True:
        try:
            await check_men_stock()
            await asyncio.sleep(random.uniform(CHECK_MIN, CHECK_MAX))
        except Exception as e:
            print("⚠️ LOOP ERROR:", e)
            await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
