from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить сайт", callback_data="add_site"),
                InlineKeyboardButton(text="Мои сайты", callback_data="my_sites"),
            ]
        ]
    )
    return keyboard
