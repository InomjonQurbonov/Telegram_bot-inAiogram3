from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

PAIRS = (
    "BTCUSDT",
    "BTCEUR",
)

ORDER_TYPE = (
    "BUY",
    "SELL",
)

def make_pairs_buttons() -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text=pair)] for pair in PAIRS]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

def make_order_buttons() -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text=order)] for order in ORDER_TYPE]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard