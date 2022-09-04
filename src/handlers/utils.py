from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.handlers.constants import all_cb, debtor_cb, payer_cb

# Map of emojis used in buttons
EMOJIS = {
    'back': '\u21A9',
    'all': '\u2714',
    'cancel': '\u274C',
    'done': '\u2705',
    'checkbox': '\u2611',
    'forward': '\u25B6',
    'backward': '\u25C0'
}


def create_payers_keyboard(balances: dict):
    """
    Create keyboard with users for choosing payer
    """

    buttons = list()
    for user in balances:
        buttons.append(InlineKeyboardButton(
            user,
            callback_data=payer_cb.new(payer=user)
        ))
    return InlineKeyboardMarkup().add(*buttons)


def create_debtors_keyboard(balances: dict, selected_debtors: list):
    """
    Create keyboard to choose debtors
    """

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
        InlineKeyboardButton(f'{EMOJIS["back"]} Назад', callback_data='back'),
        InlineKeyboardButton(f'{EMOJIS["all"]} Все', callback_data=all_cb.new(all='all')),
        InlineKeyboardButton(f'{EMOJIS["cancel"]} Отмена', callback_data='cancel'),
        InlineKeyboardButton(f'{EMOJIS["done"]} Готово', callback_data='done_debtors')
    ]
    keyboard = InlineKeyboardMarkup(row_width=len(user_buttons)).add(*user_buttons)
    keyboard.row(*tech_buttons)
    return keyboard


def create_comment_keyboard():
    """
    Create keyboard to choose if you need comment or not
    """

    buttons = [
        InlineKeyboardButton('Yes', callback_data='comment'),
        InlineKeyboardButton('No', callback_data='finish')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    tech_buttons = [
        InlineKeyboardButton(f'{EMOJIS["back"]} Назад', callback_data='back_sum'),
        InlineKeyboardButton(f'{EMOJIS["cancel"]} Отмена', callback_data='cancel')
    ]
    keyboard.row(*tech_buttons)
    return keyboard


def create_debts_payments_confirmation_keyboard():
    """
    Create keyboard to confirm debts payback when all calculations finished
    """

    transfers_buttons = [
        InlineKeyboardButton(f'{EMOJIS["done"]} Все долги выплачены!', callback_data='payed_all'),
        InlineKeyboardButton(f'{EMOJIS["back"]} Отменить и продолжить', callback_data='cancel')
    ]
    return InlineKeyboardMarkup().add(*transfers_buttons)


def create_confirmation_keyboard(payment: dict):
    """
    Create keyboard to confirm payment add
    """

    message_txt = f'Payment:\n\n{payment["payer"]} payed for {", ".join(payment["debtors"])}\n\n' \
                  f'Sum: {payment["sum"]}\n\nComment: {payment["comment"]}'
    message_txt = f'Платеж:\n\n{payment["payer"]} заплатил за {", ".join(payment["debtors"])}\n\n' \
                  f'Сумма: {payment["sum"]}\n\nКомментарий: {payment["comment"]}'
    buttons = [
        InlineKeyboardButton(f'{EMOJIS["done"]} Подтвердить', callback_data='confirm'),
        InlineKeyboardButton(f'{EMOJIS["cancel"]} Отмена', callback_data='cancel')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    return message_txt, keyboard


def create_cancel_keyboard():
    """
    Create keyboard to cancel any action
    """

    cancel_btn = InlineKeyboardButton(f'{EMOJIS["cancel"]} Отмена', callback_data='cancel')
    return InlineKeyboardMarkup().add(cancel_btn)


def edit_user_state_for_debtors(debtors_state: list, callback_data: dict, balances_users: list):
    """
    Edit state in order to change keyboard layout view. Add selected (or all) to user state
    """

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
