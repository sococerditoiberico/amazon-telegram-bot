import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

# Bot token desde variable de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# URL de tu API en Render
API_URL = "https://amazon-backend-47xw.onrender.com/products"

# Afiliado Amazon
AFFILIATE_TAG = "crdt25-21"

# Regex para extraer ASIN
ASIN_REGEX = re.compile(r"(?:dp/|dp%2F|product/|ASIN=)([A-Z0-9]{10})", re.IGNORECASE)


def extract_asin(text):
    match = ASIN_REGEX.search(text)
    if match:
        return match.group(1).upper()

    if re.fullmatch(r"[A-Z0-9]{10}", text.strip()):
        return text.strip().upper()

    return None


def scrape_amazon(asin):
    url = f"https://www.amazon.es/dp/{asin}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    title_tag = soup.find(id="productTitle")
    title = title_tag.get_text(strip=True) if title_tag else "Producto Amazon"

    image_tag = soup.find(id="landingImage")
    image_url = image_tag.get("src") if image_tag else None

    price_tag = soup.find(id="priceblock_ourprice") or soup.find(id="priceblock_dealprice")
    price = price_tag.get_text(strip=True) if price_tag else "No disponible"

    affiliate_url = f"https://www.amazon.es/dp/{asin}/?tag={AFFILIATE_TAG}"

    return {
        "title": title,
        "asin": asin,
        "amazon_url": url,
        "affiliate_url": affiliate_url,
        "image_url": image_url,
        "price": price,
    }


def send_to_api(product):
    r = requests.post(API_URL, json=product)
    return r.json()


def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hola! Envíame un ASIN o un enlace de Amazon y lo procesaré 🚀")


def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    asin = extract_asin(text)

    if not asin:
        update.message.reply_text("❌ No encontré un ASIN válido. Envíame un enlace o ASIN de Amazon.")
        return

    update.message.reply_text(f"🔍 Buscando producto {asin}...")

    product = scrape_amazon(asin)
    if not product:
        update.message.reply_text("⚠️ No pude obtener datos del producto.")
        return

    update.message.reply_text("📡 Enviando a la web...")

    response = send_to_api(product)

    update.message.reply_text(f"✅ Producto añadido!\n🔗 {response['product_page']}")


def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
