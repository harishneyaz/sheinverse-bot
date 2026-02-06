import asyncio, aiohttp, json, time
from verse_category import get_verse_men
from verse_product import get_sizes
from telegram_alert import send

DATA_FILE = "data.json"

def load():
    try: return json.load(open(DATA_FILE))
    except: return {}

def save(d):
    json.dump(d, open(DATA_FILE, "w"))

async def main():
    db = load()
    last_heartbeat = 0
    burst = False

    async with aiohttp.ClientSession() as session:
        await send(
            "🤖 SHEIN VERSE BOT STARTED\n"
            "Focus: MEN only\n"
            "Alerts: New + Restock (ALL sizes)"
        )

        while True:
            men_products = await get_verse_men(session)

            for p in men_products:
                sizes = await get_sizes(session, p["id"])
                for size, stock in sizes.items():
                    key = f"{p['id']}_{size}"
                    old = db.get(key, 0)

                    if stock > 0 and old == 0:
                        burst = True
                        await send(
                            f"🔥 SHEIN VERSE – MEN 🔥\n\n"
                            f"{p['name']}\n"
                            f"Size: {size}\n"
                            f"Price: ₹{p['price']}\n\n"
                            f"🛒 BUY NOW 👇\n{p['url']}",
                            image=p["image"]
                        )
                    db[key] = stock

            save(db)

            if time.time() - last_heartbeat > 7200:
                await send("⏰ Bot running | SHEIN VERSE MEN monitoring active ✅")
                last_heartbeat = time.time()

            await asyncio.sleep(5 if burst else 60)

asyncio.run(main())
