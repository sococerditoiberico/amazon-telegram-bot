import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

API_URL = "https://amazon-backend-47xw.onrender.com/products"
AFFILIATE_TAG = "crdt25-21"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

ASIN_REGEX = re.compile(r"(?:dp/|product/|ASIN=)([A-Z0-9]{10})", re.IGNORECASE)


def extract_asin(text: str):
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

    price_tag = (
        soup.find(id="priceblock_ourprice") or
        soup.find(id="priceblock_dealprice")
    )
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Envíame un ASIN o enlace de Amazon y lo proceso 🚀")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    asin = extract_asin(text)

    if not asin:
        await update.message.reply_text("❌ Ese texto no contiene un ASIN válido.")
        return

    await update.message.reply_text(f"🔍 Buscando información de {asin}...")

    product = scrape_amazon(asin)
    if product is None:
        await update.message.reply_text("⚠️ No pude obtener los datos del producto.")
        return

    await update.message.reply_text("📡 Subiendo a tu backend...")

    response = send_to_api(product)

    await update.message.reply_text(
        f"✅ Producto añadido!\n🔗 Enlace: {response['product_page']}"
    )


async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot iniciado! 🚀")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
