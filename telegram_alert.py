import os
from telegram import Bot

bot = Bot(token=os.getenv("BOT_TOKEN"))
CHAT_ID = os.getenv("CHAT_ID")

async def send(text, image=None):
    if image:
        await bot.send_photo(chat_id=CHAT_ID, photo=image, caption=text)
    else:
        await bot.send_message(chat_id=CHAT_ID, text=text)
