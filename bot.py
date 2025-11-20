import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# URL de tu API en Render
API_URL = "https://amazon-backend-47xw.onrender.com/products"

# Tag de afiliado
AFFILIATE_TAG = "crdt25-21"

# Token del bot (Render lo mete como variable de entorno)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Regex para extraer ASIN de enlaces o texto
ASIN_REGEX = re.compile(r"(?:dp/|dp%2F|product/|ASIN=)([A-Z0-9]{10})", re.IGNORECASE)


def extract_asin(text):
    """Extrae el ASIN de un link o texto simple."""
    match = ASIN_REGEX.search(text)
    if match:
        return match.group(1).upper()

    if re.fullmatch(r"[A-Z0-9]{10}", text.strip()):
        return text.strip().upper()

    return None


def scrape_amazon(asin):
    """Scrapea título, precio e imagen desde Amazon."""
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
    """Envía el producto al backend."""
    r = requests.post(API_URL, json=product)
    return r.json()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Envíame un ASIN o enlace de Amazon y lo convierto para tu web 🚀")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    asin = extract_asin(text)

    if not asin:
        await update.message.reply_text("❌ Ese texto no contiene un ASIN válido.")
        return

    await update.message.reply_text(f"🔍 Buscando información de {asin}...")

    product = scrape_amazon(asin)

    if not product:
        await update.message.reply_text("⚠️ No pude obtener los datos del producto.")
        return

    await update.message.reply_text("📡 Subiendo a la web...")

    response = send_to_api(product)

    # Respuesta final
    await update.message.reply_text(
        f"✅ Producto añadido correctamente!\n"
        f"🔗 Enlace en tu web: {response['product_page']}"
    )


async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

