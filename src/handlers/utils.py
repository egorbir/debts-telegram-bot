from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

from src.handlers.constants import payer_cb, debtor_cb


EMOJIS = {
    'back': '\u21A9',
    'all': '\u2714',
    'cancel': '\u274C',
    'done': '\u2705',
    'checkbox': '\u2611'
}


def create_payers_keyboard(balances: dict):
    buttons = list()
    for user in balances:
        buttons.append(InlineKeyboardButton(
            user,
            callback_data=payer_cb.new(payer=user)
        ))
    return InlineKeyboardMarkup().add(*buttons)


def create_debtors_keyboard(balances: dict, selected_debtors: list):
    user_buttons = list()
    for user in balances:
        if user in selected_debtors:
            btn_txt = f'{EMOJIS["checkbox"]} {user}'
        else:
            btn_txt = user
        user_buttons.append(
            InlineKeyboardButton(btn_txt, callback_data=debtor_cb.new(debtor=user))
        )
    tech_buttons = [
        InlineKeyboardButton(f'{EMOJIS["back"]} Back', callback_data='back'),
        InlineKeyboardButton(f'{EMOJIS["all"]} All', callback_data='all_debtors'),
        InlineKeyboardButton(f'{EMOJIS["cancel"]} Cancel', callback_data='cancel'),
        InlineKeyboardButton(f'{EMOJIS["done"]} Done', callback_data='done_debtors')
    ]
    keyboard = InlineKeyboardMarkup(row_width=len(user_buttons)).add(*user_buttons)
    keyboard.row(*tech_buttons)
    return keyboard
