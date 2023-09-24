import os
from dotenv import load_dotenv
import logging
import html
import json
import logging
import traceback
from typing import List, Tuple, cast
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InvalidCallbackData,
    PicklePersistence,
)
import requests
import time

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()

DEVELOPER_CHAT_ID = os.getenv('Developer_chat_id')

# Define a list of cryptocurrency symbols
crypto_symbols = ["BTC", "ETH", "USDT", "BNB", "XRP", "USDC", "DOGE", "LTC"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! I am your crypto pricing bot. Use me with help of following commands.\n \n /start \n \n /list")

async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton(symbol, callback_data=symbol)
            for symbol in crypto_symbols[i : i + 2]  # Display 2 buttons per row
        ]
        for i in range(0, len(crypto_symbols), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please Select the Currency: ", reply_markup=reply_markup)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    crypto = query.data
    # crypto = context.args[0] 
    # Define your API Key
    api_key = os.getenv('apt_key')

    # Construct the API URL for a specific cryptocurrency (e.g., Bitcoin)
    url = (f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={crypto}')

    # Include your API Key in the custom header
    headers = {'X-CMC_PRO_API_KEY': api_key}

    # Make the HTTP GET request
    r = requests.get(url, headers=headers)
    # r = requests.get(f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={crypto}/')
    data = r.json()
    price = data['data'][crypto]['quote']['USD']['price']
    pp = round(price,2)
    await context.bot.send_message(chat_id=update._effective_message.chat_id , reply_markup=ReplyKeyboardRemove(), text=f'The current price of {crypto} is ${pp}.')

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    invite_link = await context.bot.export_chat_invite_link(chat_id)
    update.message.reply_text(f"Here is my invite link to join this group: {invite_link}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


async def bad_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Raise an error to trigger the error handler."""
    await context.bot.wrong_method_name()  # type: ignore[attr-defined]



def main() -> None:
    """Run the bot."""
    # We use persistence to demonstrate how buttons can still work after the bot was restarted
    persistence = PicklePersistence(filepath="arbitrarycallbackdatabot")
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(os.getenv('Bot_Token'))
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list))
    application.add_handler(CommandHandler("add", join))
    application.add_handler(CommandHandler("bad_command", bad_command))
    application.add_handler(CallbackQueryHandler(price))
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


    # update_prices()

if __name__ == "__main__":
    main()
    
 # Start looping price updates
