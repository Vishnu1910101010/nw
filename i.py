import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# 🔒 Replace with your Telegram bot token (DO NOT SHARE IT PUBLICLY)
BOT_TOKEN = "8130664326:AAHDpGNSnaF4lb2DlU6psTtuQsTuYB5K2-I"

def get_terabox_download_link(terabox_url):
    """Uses Selenium to extract the direct download link from TeraBox."""
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

        if "terabox.com" not in final_url:
            return "❌ Invalid TeraBox link. Please send a correct one."

        # Scrape page content
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        download_link = None

        # Look for the direct download link
        for script in soup.find_all("script"):
            if "dlbutton" in script.text:
                match = re.search(r'href="(https://[^"]+)"', script.text)
                if match:
                    download_link = match.group(1)
                    break

        return download_link if download_link else "❌ No direct download link found."
    except Exception as e:
        return f"⚠️ Error extracting link: {str(e)}"
    finally:
        driver.quit()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("👋 Send me a **TeraBox link**, and I'll fetch the **direct download link** for you!")

async def handle_message(update: Update, context: CallbackContext):
    """Handles user messages and processes TeraBox links."""
    user_message = update.message.text

    if "terabox.com" in user_message or "teraboxlink.com" in user_message:
        await update.message.reply_text("🔍 Fetching the **direct download link**...")
        direct_link = get_terabox_download_link(user_message)

        if direct_link.startswith("http"):
            await update.message.reply_text(f"✅ **Download Link:**\n{direct_link}")
        else:
            await update.message.reply_text(direct_link)
    else:
        await update.message.reply_text("❌ Please send a **valid TeraBox link**.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
