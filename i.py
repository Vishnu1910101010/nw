import time
import os
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# 🔒 Replace with your Telegram bot token
BOT_TOKEN = "8130664326:AAHDpGNSnaF4lb2DlU6psTtuQsTuYB5K2-I"

def get_terabox_download_link(terabox_url):
    """Uses Selenium to extract the direct download link from TeraBox or TeraShare."""
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(terabox_url)
        time.sleep(5)  # Wait for JavaScript to load

        # Extract final redirected URL
        final_url = driver.current_url
        print(f"Resolved URL: {final_url}")

        if not any(domain in final_url for domain in ["terabox.com", "teraboxlink.com", "terasharelink.com"]):
            return None

        # Scrape page content
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        download_link = None

        # Search for video download link in scripts
        for script in soup.find_all("script"):
            if "downloadUrl" in script.text or "dlbutton" in script.text:
                match = re.search(r'https://[^\s"]+\.mp4', script.text)
                if match:
                    download_link = match.group(0)
                    break

        print(f"Extracted Download Link: {download_link}")
        return download_link
    except Exception as e:
        print(f"Error extracting link: {str(e)}")
        return None
    finally:
        driver.quit()

def download_video(video_url, filename="video.mp4"):
    """Downloads the video from the given URL."""
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

        return filename
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("👋 Send me a **TeraBox or TeraShare link**, and I'll download the video for you!")

async def handle_message(update: Update, context: CallbackContext):
    """Handles user messages and downloads TeraBox videos."""
    user_message = update.message.text.strip()

    # Validate link format
    terabox_pattern = r"https?://(www\.)?(terabox\.com|teraboxlink\.com|terasharelink\.com)/[^\s]+"
    match = re.search(terabox_pattern, user_message)

    if match:
        terabox_url = match.group(0)
        await update.message.reply_text("🔍 Fetching the **direct download link**...")
        video_url = get_terabox_download_link(terabox_url)

        if video_url:
            await update.message.reply_text(f"⬇️ Downloading video...")

            filename = download_video(video_url)

            if filename:
                await update.message.reply_video(video=open(filename, "rb"))
                os.remove(filename)  # Clean up after sending
            else:
                await update.message.reply_text("❌ Failed to download the video.")
        else:
            await update.message.reply_text("❌ No direct video link found.")
    else:
        await update.message.reply_text("❌ Please send a **valid TeraBox or TeraShare link**.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
