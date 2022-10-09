from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.handlers.constants import DB, DeletePayment, RDS, delete_cb
from src.handlers.utils import create_found_payments_keyboard


async def start_payment_delete(msg: types.Message):
    """
    Start the dialog for payment deletion
    """

    chat_id = str(msg.chat.id)
    group_name = RDS.get_chat_debts_group_name(chat_id=chat_id)
    payments = DB.get_all_chat_group_payments(chat_id=chat_id, group_name=group_name)["payments"]
    if len(payments) == 0:
        message = "No payments yet"
        await msg.answer(message)
    else:
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton("Yes", callback_data="delete_history_yes"),
            InlineKeyboardButton("No", callback_data="delete_history_no")
        ])
        await msg.answer("Searching payments by comment. Show the history?", reply_markup=keyboard)
        await DeletePayment.waiting_for_history_choose.set()


async def show_payment_history_for_delete(call: types.CallbackQuery):
    """
    Show all payments history before start of the search
    """

    chat_id = str(call.message.chat.id)
    group_name = RDS.get_chat_debts_group_name(chat_id=chat_id)
    payments = DB.get_all_chat_group_payments(chat_id=chat_id, group_name=group_name)["payments"]
    history_reply_template = "History:\n"
    for p in payments:
        history_reply_template += f'\n{p["date"]} - Payed: {p["payer"]} for {", ".join(p["debtors"])} - {p["sum"]}' \
                                  f'\nComment - {p["comment"]}' \
                                  f'\n____________________________'
    await call.message.edit_text(history_reply_template)
    await call.message.answer("Enter comment for search")
    await DeletePayment.waiting_for_comment.set()
    await call.answer()


async def start_search_enter_without_history(call: types.CallbackQuery):
    """
    Get user comment enter to find payment
    """

    await call.message.edit_text("Enter comment for search")
    await DeletePayment.waiting_for_comment.set()
    await call.answer()


async def comment_search_enter(msg: types.Message, state: FSMContext):
    """
    Start searching for payment by entered comment and show the result
    """

    chat_id = str(msg.chat.id)
    group_name = RDS.get_chat_debts_group_name(chat_id=chat_id)
    payments = DB.get_all_chat_group_payments(chat_id=chat_id, group_name=group_name)["payments"]
    matching = [p for p in payments if msg.text.lower() in p["comment"].lower()]
    search_reply_template = "Found:\n"
    for i, p in enumerate(matching):
        search_reply_template += f'<b>{i+1}</b>. {p["date"]} - Payed: {p["payer"]} за {", ".join(p["debtors"])} - ' \
                                 f'{p["sum"]} \nComment - {p["comment"]}' \
                                 f'\n____________________________\n'
    if len(matching) == 0:
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton("Enter another comment", callback_data="restart_search"),
            InlineKeyboardButton("Cancel", callback_data="cancel")
        ])
        await msg.answer("Nothing found!", reply_markup=keyboard)
    elif len(matching) == 1:
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton("Yes", callback_data=delete_cb.new(payment=matching[0]["id"])),
            InlineKeyboardButton("Cancel", callback_data="cancel")
        ])
        message = f"Found one payment\n\n" \
                  f'{matching[0]["date"]} - Payed: {matching[0]["payer"]} for {", ".join(matching[0]["debtors"])} - ' \
                  f'{matching[0]["sum"]} \nComment - {matching[0]["comment"]} \n\n' \
                  f'Delete?'
        await msg.answer(message, reply_markup=keyboard)
        await DeletePayment.waiting_for_confirm.set()
    else:
        await state.update_data(found_payments=matching)
        await msg.answer(f"Found {len(matching)} payments")
        await msg.answer(search_reply_template, parse_mode=types.ParseMode.HTML)
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton("Yes", callback_data="yes_new_search"),
            InlineKeyboardButton("No", callback_data="no_new_search")
        ])
        await msg.answer("Refine search?", reply_markup=keyboard)
        await DeletePayment.waiting_for_search_restart.set()


async def select_payment_from_found(call: types.CallbackQuery, state: FSMContext):
    """
    Get user enter of number to choose payment to delete
    """

    user_state_data = await state.get_data()
    await call.message.edit_text(
        text="Select the number",
        reply_markup=create_found_payments_keyboard(found_payments=user_state_data["found_payments"])
    )
    await DeletePayment.waiting_choose_number.set()
    await call.answer()


async def delete_selected_payment(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    """
    Delete payment with the number entered by user
    """

    chat_id = str(call.message.chat.id)
    payment_id = callback_data["payment"]
    group_name = RDS.get_chat_debts_group_name(chat_id=chat_id)
    payment = DB.get_chat_group_payment_by_id(chat_id=chat_id, group_name=group_name, payment_id=payment_id)
    DB.delete_chat_group_payment(
        chat_id=chat_id,
        group_name=group_name,
        payment_id=payment_id
    )
    RDS.delete_chat_payment_update_balances(chat_id=call.message.chat.id, payment=payment)
    await call.message.edit_text(f"Payment Deleted!")
    await state.finish()


def register_delete_handlers(dp: Dispatcher):
    dp.register_message_handler(
        start_payment_delete, chat_type=types.ChatType.GROUP, commands="delete", state="*"
    )
    dp.register_callback_query_handler(
        show_payment_history_for_delete, Text("delete_history_yes"), chat_type=types.ChatType.GROUP,
        state=DeletePayment.waiting_for_history_choose
    )
    dp.register_callback_query_handler(
        start_search_enter_without_history, Text("delete_history_no"), chat_type=types.ChatType.GROUP,
        state=DeletePayment.waiting_for_history_choose
    )
    dp.register_callback_query_handler(
        start_search_enter_without_history, Text("restart_search"), chat_type=types.ChatType.GROUP,
        state=DeletePayment.waiting_for_comment
    )
    dp.register_message_handler(
        comment_search_enter, state=DeletePayment.waiting_for_comment, chat_type=types.ChatType.GROUP
    )
    dp.register_callback_query_handler(
        select_payment_from_found, Text("no_new_search"), state=DeletePayment.waiting_for_search_restart,
        chat_type=types.ChatType.GROUP
    )
    dp.register_callback_query_handler(
        start_search_enter_without_history, Text("yes_new_search"), state=DeletePayment.waiting_for_search_restart,
        chat_type=types.ChatType.GROUP
    )

    dp.register_callback_query_handler(
        delete_selected_payment, delete_cb.filter(),
        state=[DeletePayment.waiting_choose_number, DeletePayment.waiting_for_confirm],
        chat_type=types.ChatType.GROUP
    )
