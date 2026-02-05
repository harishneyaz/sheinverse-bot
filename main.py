import asyncio
import aiohttp
import random
import os
import sys
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================== BASIC LOG ==================
print("🚀 Container booting...")

# ================== ENV CHECK ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ ERROR: TELEGRAM_TOKEN or CHAT_ID missing")
    sys.exit(1)

print("✅ ENV loaded")

# ================== CONFIG ==================
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

# ================== FETCH PRODUCTS ==================
async def fetch_products(cat_id):
    params = {
        "cat_id": cat_id,
        "page": 1,
        "page_size": 60,
        "country": "IN",
        "language": "en",
        "currency": "INR"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, headers=HEADERS, params=params, timeout=20) as r:
            data = await r.json()
            return data.get("goods_list", [])

# ================== ALERT ==================
async def send_alert(product, title):
    try:
        link = f"https://sheinindia.in/{product['goods_url']}"
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=product["goods_img"],
            caption=f"""{title}

👕 {product['goods_name']}
💰 ₹{product['sale_price']}
🔗 Buy Now:
{link}

⚡ FAST BUY
"""
        )
    except Exception as e:
        print("⚠️ Alert error:", e)

# ================== MEN STOCK CHECK ==================
async def check_men_stock():
    products = await fetch_products(MEN_CAT_ID)

    for p in products:
        pid = p["goods_id"]
        in_stock = p["stock"] > 0

        if pid not in LAST_STATE:
            LAST_STATE[pid] = in_stock
            if in_stock:
                print("🆕 New product detected:", pid)
                await send_alert(p, "🆕 NEW MEN STOCK")
        else:
            if LAST_STATE[pid] is False and in_stock is True:
                LAST_STATE[pid] = True
                print("🔁 Restock detected:", pid)
                await send_alert(p, "🔁 MEN RESTOCK")

# ================== SUMMARY ==================
async def send_summary():
    men = await fetch_products(MEN_CAT_ID)
    women = await fetch_products(WOMEN_CAT_ID)

    men_count = sum(1 for p in men if p["stock"] > 0)
    women_count = sum(1 for p in women if p["stock"] > 0)

    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"""📊 SHEIN VERSE STATUS

👨 Men in stock: {men_count}
👩 Women in stock: {women_count}

⏱ Bot running smooth ✅
"""
    )

# ================== MAIN LOOP ==================
async def main():
    print("🤖 Bot starting...")

    await bot.send_message(
        chat_id=CHAT_ID,
        text="🤖 SHEIN VERSE STOCK BOT STARTED\nFetching current stock…"
    )

    await send_summary()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_summary, "interval", hours=2)
    scheduler.start()

    print("✅ Scheduler started")

    while True:
        try:
            await check_men_stock()
            sleep_time = random.uniform(CHECK_MIN, CHECK_MAX)
            print(f"⏱ Sleeping {int(sleep_time)} sec")
            await asyncio.sleep(sleep_time)
        except Exception as e:
            print("❌ LOOP ERROR:", e)
            await asyncio.sleep(15)

# ================== ENTRY ==================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("🔥 FATAL ERROR:", e)
        sys.exit(1)
