import asyncio
import requests
from bs4 import BeautifulSoup
import telebot
import os
import json
import threading

# ----------------------------- CONFIG -----------------------------
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Telegram bot token
CHAT_ID = os.getenv('CHAT_ID')      # Your Telegram chat ID
SHEIN_URL = os.getenv('SHEIN_URL', 'https://sheinindia.in/sheinverse/c/sverse-5939-37961')

bot = telebot.TeleBot(BOT_TOKEN)
STOCK_FILE = 'previous_stock.json'

# ------------------------ HELPER FUNCTIONS -----------------------
def load_previous_stock():
    """Load previously checked stock"""
    if os.path.exists(STOCK_FILE):
        with open(STOCK_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_stock(stock):
    """Save current stock to file"""
    with open(STOCK_FILE, 'w') as f:
        json.dump(stock, f)

def fetch_shein_products():
    """Fetch Shein Verse products using requests + BeautifulSoup"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    r = requests.get(SHEIN_URL, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    products = {}
    men_count = 0
    women_count = 0

    for item in soup.find_all('div', class_='product-item'):
        title_elem = item.find('h3') or item.find('a', class_='title')
        title = title_elem.text.strip() if title_elem else 'Unknown'
        
        link_elem = item.find('a', href=True)
        link = f"https://sheinindia.in{link_elem['href']}" if link_elem else None
        img_elem = item.find('img')
        image_url = img_elem['src'] if img_elem else None
        stock_elem = item.find('span', class_='stock-status') or item.find('div', class_='out-of-stock')
        status = 'Out of Stock' if stock_elem and 'out' in stock_elem.text.lower() else 'In Stock'
        
        # Count men/women
        if 'men' in title.lower():
            men_count += 1
        elif 'women' in title.lower():
            women_count += 1
        
        product_id = link or title
        products[product_id] = {
            'title': title, 'status': status, 'link': link, 'image': image_url
        }
    
    return products, men_count, women_count

# ------------------------ MEN ALERTS -----------------------------
async def men_alert_checker():
    """Check men’s stock every 1 second and send single combined alert message"""
    previous_stock = load_previous_stock()
    
    while True:
        try:
            current_stock, men_count, women_count = fetch_shein_products()
            
            # Find all men’s products that are in stock and were not previously in stock
            new_men_products = []
            for pid, info in current_stock.items():
                prev_status = previous_stock.get(pid, {}).get('status', 'Out of Stock')
                if info['status'] == 'In Stock' and prev_status != 'In Stock' and 'men' in info['title'].lower():
                    new_men_products.append(info)
            
            # Send a single message for all new men’s products
            if new_men_products:
                message_text = "🚨 New/Restocked Men's Products:\n\n"
                for idx, prod in enumerate(new_men_products, 1):
                    message_text += f"{idx}. {prod['title']}\nBuy: {prod['link']}\n\n"
                
                # Telegram has a 4096 character limit, so we may need to split messages
                for chunk_start in range(0, len(message_text), 4000):
                    bot.send_message(CHAT_ID, message_text[chunk_start:chunk_start+4000])
                
                # Send images (optional: can also send as media group)
                for prod in new_men_products:
                    if prod['image']:
                        try:
                            bot.send_photo(CHAT_ID, prod['image'], caption=prod['title'])
                        except:
                            continue  # skip if image fails
            
            # Update previous stock
            save_stock(current_stock)
            previous_stock = current_stock
            
        except Exception as e:
            print("Error checking Shein:", e)
        
        await asyncio.sleep(1)  # 1-second interval

# ------------------------ STOCK SUMMARY --------------------------
async def summary_sender():
    """Send stock summary of both men and women every 2 hours"""
    while True:
        try:
            _, men_count, women_count = fetch_shein_products()
            summary_message = f"📊 Current Stock Summary:\nMen: {men_count}\nWomen: {women_count}"
            bot.send_message(CHAT_ID, summary_message)
        except Exception as e:
            print("Error sending summary:", e)
        
        await asyncio.sleep(2 * 60 * 60)  # Every 2 hours

# ------------------------ BOT HANDLER ----------------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 Shein India Verse Bot started!\n"
                                      "Monitoring men's stock every 1 second and sending 2-hour summaries...")
    # Run both tasks
    asyncio.run(asyncio.gather(men_alert_checker(), summary_sender()))

# ------------------------ MAIN ----------------------------
if __name__ == "__main__":
    # Run bot polling in a separate thread
    threading.Thread(target=lambda: bot.polling(none_stop=True)).start()
    # Run async tasks
    asyncio.run(asyncio.gather(men_alert_checker(), summary_sender()))
