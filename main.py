import asyncio
import json
import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import telebot
import schedule
import requests
from bs4 import BeautifulSoup

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables (set in Railway)
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SHEIN_URL = os.getenv('SHEIN_URL', 'https://sheinindia.in/sheinverse/c/sverse-5939-37961?srsltid=AfmBOoo3IkxXIYV7-8wbcMa6PRHTTBoWaU6VVPNFOGUL9u0znLslb2s8#filterBy')  # Updated to Shein India Verse URL

bot = telebot.TeleBot(BOT_TOKEN)

# File for storing previous stock
STOCK_FILE = 'previous_stock.json'
# File for check counter
COUNTER_FILE = 'check_counter.json'

def load_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            return json.load(f).get('count', 0)
    return 0

def save_counter(count):
    with open(COUNTER_FILE, 'w') as f:
        json.dump({'count': count}, f)

def load_previous_stock():
    if os.path.exists(STOCK_FILE):
        with open(STOCK_FILE, 'r') as f:
            return json.load(f)
    return {'men': 0, 'women': 0, 'products': {}}

def save_stock(stock):
    with open(STOCK_FILE, 'w') as f:
        json.dump(stock, f)

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    return driver

async def scrape_stock():
    driver = setup_driver()
    try:
        logging.info("Starting stock scrape for Shein India Verse...")
        driver.get(SHEIN_URL)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-item')))  # Adjust class if needed for India site
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        products = soup.find_all('div', class_='product-item')  # Inspect Shein's HTML for exact class
        men_count = 0
        women_count = 0
        current_products = {}
        alerts = []
        
        for product in products:
            title_elem = product.find('h3') or product.find('a', class_='title')
            title = title_elem.text.strip() if title_elem else 'Unknown'
            stock_elem = product.find('span', class_='stock-status') or product.find('div', class_='out-of-stock')
            stock_status = 'Out of Stock' if stock_elem and 'out' in stock_elem.text.lower() else 'In Stock'
            image_elem = product.find('img')
            image_url = image_elem['src'] if image_elem else None
            link_elem = product.find('a', href=True)
            buy_link = f"https://sheinindia.in{link_elem['href']}" if link_elem else None
            
            # Focus on men's items in Verse
            if 'men' in title.lower():
                men_count += 1
                product_id = hash(title)  # Simple ID for tracking
                current_products[product_id] = {'title': title, 'status': stock_status, 'image': image_url, 'link': buy_link}
                
                prev_status = load_previous_stock().get('products', {}).get(product_id, {}).get('status', 'Out of Stock')
                if stock_status == 'In Stock' and prev_status != 'In Stock':
                    alerts.append({
                        'title': title,
                        'image': image_url,
                        'link': buy_link
                    })
            elif 'women' in title.lower():
                women_count += 1
        
        summary = {'men': men_count, 'women': women_count, 'products': current_products}
        logging.info("Stock scrape for Shein India Verse completed successfully.")
        return summary, alerts
    except Exception as e:
        logging.error(f"Scraping error for Shein India Verse: {e}")
        return load_previous_stock(), []  # Fallback to previous
    finally:
        driver.quit()

async def send_alert(alerts):
    for alert in alerts:
        try:
            if alert['image']:
                # Download and send image
                img_response = requests.get(alert['image'])
                if img_response.status_code == 200:
                    with open('temp_img.jpg', 'wb') as f:
                        f.write(img_response.content)
                    with open('temp_img.jpg', 'rb') as f:
                        bot.send_photo(CHAT_ID, f, caption=f"🚨 New/Restocked Men's Item in Shein India Verse: {alert['title']}\nBuy: {alert['link']}")
                    os.remove('temp_img.jpg')
                else:
                    bot.send_message(CHAT_ID, f"🚨 New/Restocked Men's Item in Shein India Verse: {alert['title']}\nBuy: {alert['link']}")
            else:
                bot.send_message(CHAT_ID, f"🚨 New/Restocked Men's Item in Shein India Verse: {alert['title']}\nBuy: {alert['link']}")
        except Exception as e:
            logging.error(f"Alert send error: {e}")

async def send_summary(summary):
    message = f"📊 Current Stock Summary in Shein India Verse:\nMen: {summary['men']}\nWomen: {summary['women']}"
    try:
        bot.send_message(CHAT_ID, message)
    except Exception as e:
        logging.error(f"Summary send error: {e}")

async def check_and_alert():
    global check_count
    check_count += 1
    save_counter(check_count)
    logging.info(f"Check #{check_count} started for Shein India Verse.")
    
    summary, alerts = await scrape_stock()
    prev_summary = load_previous_stock()
    
    # Send alerts for men's changes
    if alerts:
        await send_alert(alerts)
    
    # Send summary every 2 hours (handled by schedule)
    await send_summary(summary)
    
    # Save updated stock
    save_stock(summary)
    logging.info(f"Check #{check_count} completed for Shein India Verse. Next check in 30 minutes.")

@bot.message_handler(commands=['start'])
def start(message):
    asyncio.run(asyncio.sleep(0))  # Ensure async context
    bot.send_message(message.chat.id, "🤖 Advanced Shein India Verse Bot Started! Monitoring Shein India Verse collection for men's stock alerts and summaries.")
    asyncio.run(check_and_alert())  # Initial check

async def run_scheduler():
    global check_count
    check_count = load_counter()  # Load initial count
    logging.info(f"Scheduler started with check count: {check_count} for Shein India Verse")
    
    schedule.every(30).minutes.do(lambda: asyncio.create_task(check_and_alert()))  # Faster checks for alerts
    schedule.every(2).hours.do(lambda: asyncio.create_task(send_summary(load_previous_stock())))  # Summary only
    
    iteration = 0
    while True:
        iteration += 1
        logging.info(f"Scheduler iteration #{iteration} running for Shein India Verse...")
        schedule.run_pending()
        await asyncio.sleep(60)  # Check every minute; logs will show if it stops here

if __name__ == "__main__":
    # Start bot polling in a thread
    import threading
    def bot_polling():
        bot.polling(none_stop=True)
    
    threading.Thread(target=bot_polling).start()
    
    # Run async scheduler
    asyncio.run(run_scheduler())
