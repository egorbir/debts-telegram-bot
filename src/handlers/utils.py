from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.handlers.constants import all_cb, debtor_cb, payer_cb

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
        InlineKeyboardButton(f'{EMOJIS["all"]} All', callback_data=all_cb.new(all='all')),
        InlineKeyboardButton(f'{EMOJIS["cancel"]} Cancel', callback_data='cancel'),
        InlineKeyboardButton(f'{EMOJIS["done"]} Done', callback_data='done_debtors')
    ]
    keyboard = InlineKeyboardMarkup(row_width=len(user_buttons)).add(*user_buttons)
    keyboard.row(*tech_buttons)
    return keyboard


def create_comment_keyboard():
    buttons = [
        InlineKeyboardButton('Yes', callback_data='comment'),
        InlineKeyboardButton('No', callback_data='finish')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    tech_buttons = [
        InlineKeyboardButton(f'{EMOJIS["back"]} Back', callback_data='back_sum'),
        InlineKeyboardButton(f'{EMOJIS["cancel"]} Cancel', callback_data='cancel')
    ]
    keyboard.row(*tech_buttons)
    return keyboard


def create_debts_payments_confirmation_keyboard():
    transfers_buttons = [
        InlineKeyboardButton(f'{EMOJIS["done"]} All debts payed!', callback_data='payed_all'),
        InlineKeyboardButton(f'{EMOJIS["back"]} Cancel and continue', callback_data='cancel')
    ]
    return InlineKeyboardMarkup().add(*transfers_buttons)


def create_confirmation_keyboard(payment: dict):
    message_txt = f'Payment:\n\n{payment["payer"]} payed for {", ".join(payment["debtors"])}\n\n' \
                  f'Sum: {payment["sum"]}\n\nComment: {payment["comment"]}'
    buttons = [
        InlineKeyboardButton(f'{EMOJIS["done"]} Confirm', callback_data='confirm'),
        InlineKeyboardButton(f'{EMOJIS["cancel"]} Cancel', callback_data='cancel')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    return message_txt, keyboard


def create_cancel_keyboard():
    cancel_btn = InlineKeyboardButton(f'{EMOJIS["cancel"]} Cancel', callback_data='cancel')
    return InlineKeyboardMarkup().add(cancel_btn)


def edit_user_state_for_debtors(debtors_state: list, callback_data: dict, balances_users: list):
    if 'all' in callback_data:
        if all(user in debtors_state for user in balances_users):
            debtors_state.clear()
        else:
            for user in balances_users:
                if user not in debtors_state:
                    debtors_state.append(user)
    elif 'debtor' in callback_data:
        if callback_data['debtor'] not in debtors_state:
            debtors_state.append(callback_data['debtor'])
        else:
            debtors_state.remove(callback_data['debtor'])

    return debtors_state
