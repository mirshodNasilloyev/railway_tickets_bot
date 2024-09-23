import logging
import os
import time

from dotenv import load_dotenv

import data
from driver_init import WebDriverHandler
from data import user_data, db, url
from datetime import date, timedelta, datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler
)

# API Keys
load_dotenv()
TOKEN = os.getenv("TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")

# Entry Constants
CHOOSE, LOCATION_FROM, LOCATION_TO, INTERVAL, DATE, SEARCH, CANCEL = range(7)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# XPATH Making
def date_xpath_converter(date_in: str) -> str:
    """ Date Converter Function, input date 12.06.2024 -> Saturday, Sentabr 12, 2024
    """
    date_obj = datetime.strptime(date_in, "%d.%m.%y")
    formatted_date = date_obj.strftime("%A, %B %d, %Y")
    date_from_xpath = f"//div[@aria-label='{formatted_date}']"
    return date_from_xpath


def xpath_list_func(req_list: dict) -> list:
    xpath_list: list = []
    from_drop_down_xpath = "//input[@placeholder='From']"
    from_drop_down_option_xpath = f"//ul[@class='search-trains__dropdown']//li[contains(text(), '{req_list['city_from']}')]"
    to_drop_down_option_xpath = f"//ul[@class='search-trains__dropdown']//li[contains(text(), '{req_list['city_to']}')]"
    calendar_icon_xpath = "//img[@alt='calendar icon']"
    date_xpath = date_xpath_converter(req_list['date'])
    search_xpath = "//button[@class='search_input_submit']"
    xpath_list.append(from_drop_down_xpath)
    xpath_list.append(from_drop_down_option_xpath)
    xpath_list.append(to_drop_down_option_xpath)
    xpath_list.append(calendar_icon_xpath)
    xpath_list.append(date_xpath)
    xpath_list.append(search_xpath)
    return xpath_list


# Keyboards
def returnHomeKeyboard():
    return [
        [
            InlineKeyboardButton("Qayerdan", callback_data="city_from"),
            InlineKeyboardButton("Qayerga", callback_data="city_to"),
        ],
        [
            InlineKeyboardButton("Interval", callback_data="interval"),
            InlineKeyboardButton("Sanani kiriting", callback_data="date"),
        ]
    ]


def returnFromKeyboard():
    return [
        [
            InlineKeyboardButton("Toshkent", callback_data="location_from:Tashkent"),
            InlineKeyboardButton("Buxoro", callback_data="location_from:Bukhara")
        ],
        [
            InlineKeyboardButton("Samarqand", callback_data="location_from:Samarkand"),
            InlineKeyboardButton("Nukus", callback_data="location_from:Nukus")
        ],
        [
            InlineKeyboardButton("Xiva", callback_data="location_from:Khiva"),
            InlineKeyboardButton("Urganch", callback_data="location_from:Urgench")
        ],
        [
            InlineKeyboardButton("Navoiy", callback_data="location_from:Navoi"),
            InlineKeyboardButton("Andijon", callback_data="location_from:Andijan")
        ],
        [
            InlineKeyboardButton("Qarshi", callback_data="location_from:Karshi"),
            InlineKeyboardButton("Jizzax", callback_data="location_from:Jizzakh")
        ],
        [
            InlineKeyboardButton("Termiz", callback_data="location_from:Termez"),
            InlineKeyboardButton("Sirdaryo", callback_data="location_from:Gulistan")
        ],
        [
            InlineKeyboardButton("Qo'qon", callback_data="location_from:Qo'qon"),
            InlineKeyboardButton("Marg'ilon", callback_data="location_from:Margilon")
        ],
        [
            InlineKeyboardButton("Pop", callback_data="location_from:Pop"),
            InlineKeyboardButton("Namangan", callback_data="location_from:Namangan")
        ]
    ]


def returnToKeyboard():
    return [
        [
            InlineKeyboardButton("Toshkent", callback_data="city_to:Tashkent"),
            InlineKeyboardButton("Buxoro", callback_data="city_to:Bukhara")
        ],
        [
            InlineKeyboardButton("Samarqand", callback_data="city_to:Samarkand"),
            InlineKeyboardButton("Nukus", callback_data="city_to:Nukus")
        ],
        [
            InlineKeyboardButton("Xiva", callback_data="city_to:Khiva"),
            InlineKeyboardButton("Urganch", callback_data="city_to:Urgench")
        ],
        [
            InlineKeyboardButton("Navoiy", callback_data="city_to:Navoi"),
            InlineKeyboardButton("Andijon", callback_data="city_to:Andijan")
        ],
        [
            InlineKeyboardButton("Qarshi", callback_data="city_to:Karshi"),
            InlineKeyboardButton("Jizzax", callback_data="city_to:Jizzakh")
        ],
        [
            InlineKeyboardButton("Termiz", callback_data="city_to:Termez"),
            InlineKeyboardButton("Sirdaryo", callback_data="city_to:Gulistan")
        ],
        [
            InlineKeyboardButton("Qo'qon", callback_data="city_to:Qo'qon"),
            InlineKeyboardButton("Marg'ilon", callback_data="city_to:Margilon")
        ],
        [
            InlineKeyboardButton("Pop", callback_data="city_to:Pop"),
            InlineKeyboardButton("Namangan", callback_data="city_to:Namangan")
        ]
    ]


def returnDateKeyboard():
    today = date.today()
    days = [(today + timedelta(days=i)).strftime('%d.%m.%y') for i in range(7)]
    keyboards = [InlineKeyboardButton(i, callback_data=f"date:{i}") for i in days]
    keyboard = [keyboards[j:j + 2] for j in range(0, len(keyboards), 2)]
    return keyboard


def returnIntervalKeyboard():
    return [
        [
            InlineKeyboardButton("1 minut", callback_data="interval:1"),
            InlineKeyboardButton("30 minut", callback_data="interval:30")
        ],
        [
            InlineKeyboardButton("1 soat", callback_data="interval:60"),
            InlineKeyboardButton("2 soat", callback_data="interval:120")
        ],

    ]


# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alekum.Bu Bot sizga poyezdlarga biletlarni osonlik bilan\n olishizga"
                                    "yordam beradi va u quyidagi buyruqlardan iborat:\n /start - Botni ishga "
                                    "tushirish\n"
                                    "/route - Yo'nalishni yaratish\n /cancel - qidiruvni to'xtatish")
    user = update.message.from_user
    logger.info("User %s started the conversation", user.first_name)


async def route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global keys_list
    data.repeat = True
    keys_list = list(user_data.keys())
    keys_list.remove("user_id")
    keyboard = returnHomeKeyboard()
    reply_markup_home = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Kerakli bo'limlarni to'ldiring", reply_markup=reply_markup_home)
    return CHOOSE


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "city_from":
        keyboard = returnFromKeyboard()
        reply_markup_from = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Qayerdan...", reply_markup=reply_markup_from)
        return LOCATION_FROM
    elif choice == "city_to":
        keyboard = returnToKeyboard()
        reply_markup_to = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Qayerga...", reply_markup=reply_markup_to)
        return LOCATION_TO
    elif choice == "interval":
        keyboard = returnIntervalKeyboard()
        reply_markup_int = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Intervalni kiriting", reply_markup=reply_markup_int)
        return INTERVAL
    elif choice == "date":
        keyboard = returnDateKeyboard()
        reply_markup_int = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Sanani kiriting", reply_markup=reply_markup_int)
        return DATE
    elif choice == "search":
        return SEARCH
    else:
        await update.message.reply_text("Siz belgilanmagan tugmani bosdiz!")


async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Handling....")
    query = update.callback_query
    user_id = query.from_user.id
    user_data["user_id"] = user_id
    await query.answer()
    data = query.data.split(':')
    print(data)
    if data[0] == "location_from":
        user_data["city_from"] = data[1]
        if "city_from" in keys_list:
            keys_list.remove("city_from")
    elif data[0] == "city_to":
        user_data["city_to"] = data[1]
        if "city_to" in keys_list:
            keys_list.remove("city_to")
    elif data[0] == "interval":
        user_data["interval"] = data[1]
        if "interval" in keys_list:
            keys_list.remove("interval")
    elif data[0] == "date":
        user_data["date"] = data[1]
        if "date" in keys_list:
            keys_list.remove("date")
    else:
        print("Error adding into dict")
    data.clear()
    print(keys_list)
    # Asosiy menuga qaytish
    keyboard = returnHomeKeyboard()

    if not keys_list:
        keyboard.append([InlineKeyboardButton("Search", callback_data="search")])
        reply_markup_home = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Barcha bo'limlar to'ldirildi qidiruvni"
                                      " boshlashiz mumkin:", reply_markup=reply_markup_home)
        return SEARCH
    else:
        reply_markup_home = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Qolgan bo'limlarni ham yo'ldiring", reply_markup=reply_markup_home)
        return CHOOSE


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Query
    query = update.callback_query
    if query.data == "cancel":
        return CANCEL
    await query.answer()
    await query.message.reply_text(f"Qidirilmoqda......")
    wd = WebDriverHandler()
    paths = xpath_list_func(user_data)
    wd.setup_driver(url)
    wd.run_driver(paths)
    wd.data_handling()
    wd.stop_driver()

    keyboard = [
        [InlineKeyboardButton('Cancel', callback_data="cancel")]
    ]
    print(db)
    if not db == []:
        post: str = ""
        for items in db:
            print(items)
            ps = (f"Poyezd turi: {items[0]}\n"
                  f"Vaqt:         {items[1]}-----------------> {items[3]}\n"
                  f"Location: {items[2]}-----------------> {items[4]}\n"
                  f"-----------------------------------------------------\n")
            post += ps
        reply_markup = InlineKeyboardMarkup(keyboard)
        add_text = (f"Biletlarni {url} ga kirib olishingiz mumkin.\n"
                    f"Hozirda post yangilanishi {user_data['interval']} minutni tashkil qilyapdi."
                    f"Yangilanishni to'xtatish uchun cancel tugmasini bosing.")
        post += add_text

        await query.edit_message_text(post, reply_markup=reply_markup)
    else:
        await query.message.reply_text(f"Poyezdlar topilmadi.")
        return CANCEL
    mini = int(user_data['interval'])
    time.sleep(mini * 60)

    return SEARCH


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Chiptalarni qidirish jarayoni bekor qilindi.')
    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    # Bot running...
    print("Bot running...")
    # Application
    app = Application.builder().token(TOKEN).build()

    # Conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('route', route)],
        states={
            CHOOSE: [CallbackQueryHandler(choose)],
            LOCATION_FROM: [CallbackQueryHandler(handle_selection)],
            LOCATION_TO: [CallbackQueryHandler(handle_selection)],
            INTERVAL: [CallbackQueryHandler(handle_selection)],
            DATE: [CallbackQueryHandler(handle_selection)],
            SEARCH: [CallbackQueryHandler(search)],
            CANCEL: [CallbackQueryHandler(cancel)]
        },
        fallbacks=[CommandHandler('route', route)]
    )

    # Commands
    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)

    # Bot polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
