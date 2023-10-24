from aiogram import types

from src.constants import EMOJIS
from src.utils.callbacks_data import all_cb, debtor_cb, delete_cb, payer_cb


def create_payers_keyboard(balances: dict):
    """
    Create keyboard with users for choosing payer
    """

    buttons = list()
    for user in balances:
        buttons.append(types.InlineKeyboardButton(
            user,
            callback_data=payer_cb.new(payer=user)
        ))
    return types.InlineKeyboardMarkup().add(*buttons)


def create_debtors_keyboard(balances: dict, selected_debtors: list):
    """
    Create keyboard to choose debtors
    """

    user_buttons = list()
    for user in balances:
        if user in selected_debtors:
            btn_txt = f"{EMOJIS['checkbox']} {user}"
        else:
            btn_txt = user
        user_buttons.append(
            types.InlineKeyboardButton(btn_txt, callback_data=debtor_cb.new(debtor=user))
        )
    tech_buttons = [
        types.InlineKeyboardButton(f"{EMOJIS['back']} Back", callback_data="back"),
        types.InlineKeyboardButton(f"{EMOJIS['all']} All", callback_data=all_cb.new(all="all")),
        types.InlineKeyboardButton(f"{EMOJIS['cancel']} Cancel", callback_data="cancel"),
        types.InlineKeyboardButton(f"{EMOJIS['done']} Done", callback_data="done_debtors")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=len(user_buttons)).add(*user_buttons)
    keyboard.row(*tech_buttons)
    return keyboard


def create_debts_payments_confirmation_keyboard():
    """
    Create keyboard to confirm debts payback when all calculations finished
    """

    transfers_buttons = [
        types.InlineKeyboardButton(f"{EMOJIS['done']} All debts are paid!", callback_data="payed_all"),
        types.InlineKeyboardButton(f"{EMOJIS['back']} Cancel and continue", callback_data="cancel")
    ]
    return types.InlineKeyboardMarkup().add(*transfers_buttons)


def create_confirmation_keyboard(payment: dict):
    """
    Create keyboard to confirm payment add
    """

    message_txt = f"Payment:\n\n{payment['payer']} payed for {', '.join(payment['debtors'])}\n\n" \
                  f"Sum: {payment['amount']}\n\nComment: {payment['comment']}"
    buttons = [
        types.InlineKeyboardButton(f"{EMOJIS['done']} Confirm", callback_data="confirm"),
        types.InlineKeyboardButton(f"{EMOJIS['cancel']} Cancel", callback_data="cancel")
    ]
    keyboard = types.InlineKeyboardMarkup().add(*buttons)
    return message_txt, keyboard


def create_cancel_keyboard():
    """
    Create keyboard to cancel any action
    """

    cancel_btn = types.InlineKeyboardButton(f"{EMOJIS['cancel']} Cancel", callback_data="cancel")
    return types.InlineKeyboardMarkup().add(cancel_btn)


def create_found_payments_keyboard(found_payments: list[dict]):
    """
    Create keyboard after search for payments to delete
    """

    payments_buttons = [
        types.InlineKeyboardButton(str(i+1), callback_data=delete_cb.new(payment=payment["id"])) for i, payment in
        enumerate(found_payments)
    ]
    keyboard = types.InlineKeyboardMarkup().add(*payments_buttons)
    return keyboard


def edit_user_state_for_debtors(debtors_state: list, callback_data: dict, balances_users: list):
    """
    Edit state in order to change keyboard layout view. Add selected (or all) to user state
    """

    if "all" in callback_data:
        if all(user in debtors_state for user in balances_users):
            debtors_state.clear()
        else:
            for user in balances_users:
                if user not in debtors_state:
                    debtors_state.append(user)
    elif "debtor" in callback_data:
        if callback_data["debtor"] not in debtors_state:
            debtors_state.append(callback_data["debtor"])
        else:
            debtors_state.remove(callback_data["debtor"])

    return debtors_state
