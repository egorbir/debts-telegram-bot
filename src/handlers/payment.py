import datetime
import re
import uuid

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.constants import DB, RDS
from src.credentials import BOT_NAME
from src.utils.balances_processing import balances_to_transfers
from src.utils.callbacks_data import all_cb, back_pay, debtor_cb, payer_cb
from src.utils.decorators import timeout
from src.utils.keyboards import EMOJIS, create_confirmation_keyboard, create_debtors_keyboard, \
    create_debts_payments_confirmation_keyboard, create_payers_keyboard, edit_user_state_for_debtors
from src.utils.state_groups import AddPayment


@timeout(state_to_cancel="AddPayment:waiting_for_payer")
async def register_payment(msg: types.Message | types.CallbackQuery, state: FSMContext):
    """
    Base start of payment add handler.
    Start of add - command '/pay', come back from payer - callback 'back'

    :param msg: either Message or Callback
    :param state: FSMContext
    :return: None
    """

    # Multipurpose handler for both "/pay" command and "back" inline button
    chat_id = msg.chat.id if isinstance(msg, types.Message) else msg.message.chat.id
    balances = RDS.get_chat_balances(chat_id=chat_id)
    if len(balances) < 3:
        message = f"Works with 3 or more people, now - {len(balances)}. " \
                  f"Use /reg command and check who is in group with /list"
        await msg.answer(message)
        return
    message = "Select who payed"
    if isinstance(msg, types.Message):
        await msg.answer(
            reply_markup=create_payers_keyboard(balances=balances), text=message
        )
    else:
        await msg.message.edit_text(
            reply_markup=create_payers_keyboard(balances=balances), text=message
        )
    await AddPayment.waiting_for_payer.set()


@timeout(state_to_cancel="AddPayment:waiting_for_debtors")
async def payer_select_callback(msg: types.CallbackQuery, state: FSMContext, callback_data: dict):
    """
    Callback after payer choose.
    First - save selected payer to user storage. Second - render interface for debtors choose

    :param msg: Callback
    :param callback_data: Callback interfaces
    :param state: redis state
    :return: None
    """

    # Save selected payer to storage
    balances = RDS.get_chat_balances(chat_id=msg.message.chat.id)
    await state.update_data(debtors=list())
    if "payer" in callback_data:
        await state.update_data(payer=callback_data["payer"])

    # Start next step rendering
    message = "Select who was the part of this payment"
    await msg.message.edit_text(
        text=message,
        reply_markup=create_debtors_keyboard(
            balances=balances,
            selected_debtors=list()
        )
    )
    await AddPayment.waiting_for_debtors.set()


async def get_debtors_callback(msg: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Callback for debtors choose. Render who are chosen or not. Save chosen to storage
    Starts on: 1 - initial render, 2 - single debtor change, 3 - select all debtors

    :param msg: Callback
    :param callback_data: Callback interfaces
    :param state: redis state
    :return: None
    """

    balances = RDS.get_chat_balances(chat_id=msg.message.chat.id)
    user_state_data = await state.get_data()
    user_state_data["debtors"] = edit_user_state_for_debtors(
        debtors_state=user_state_data["debtors"],
        callback_data=callback_data,
        balances_users=list(balances.keys())
    )
    message = "Select who was the part of this payment"
    await state.update_data(debtors=user_state_data["debtors"])
    await msg.message.edit_text(
        text=message,
        reply_markup=create_debtors_keyboard(
            balances=balances,
            selected_debtors=user_state_data["debtors"]
        )
    )


@timeout(state_to_cancel="AddPayment:waiting_for_sum")
async def done_select_callback(msg: types.CallbackQuery, state: FSMContext):
    """
    Callback on done button after all debtors are chosen.
    Render interface for payment amount enter

    :param msg: Callback
    :param state: redis state
    :return: None
    """

    user_state_data = await state.get_data()
    if len(user_state_data["debtors"]) == 0:
        message = "No one chosen"
        await msg.answer(message)
    else:
        sum_message = "Enter amount of payment:"
        keyboard = InlineKeyboardMarkup().add(
            *[
                InlineKeyboardButton(f"{EMOJIS['back']} Back", callback_data=back_pay.new()),
                InlineKeyboardButton(f"{EMOJIS['cancel']} Cancel", callback_data="cancel")
            ]
        )
        await msg.message.edit_text(text=sum_message, reply_markup=keyboard)
        await AddPayment.waiting_for_sum.set()


@timeout(state_to_cancel="AddPayment:waiting_for_comment")
async def get_payment_amount(msg: types.Message, state: FSMContext):
    """
    Recognize payment amount, save to storage. Render interface for comment input

    :param msg: Message
    :param state: redis storage
    :return: None
    """

    pattern = r"\d+(\,\d*)?$"

    if re.match(pattern, msg.text.replace(".", ",")) and float(msg.text) != 0:
        payment_amount = round(float(msg.text.replace(",", ".")), ndigits=2)
        await state.update_data(payment_amount=payment_amount)
        await AddPayment.waiting_for_comment.set()
        message = "Enter comment"
        await msg.answer(text=message)
    else:
        message = "Payment amount is not valid. Repeat"
        await msg.answer(message)


@timeout(state_to_cancel="AddPayment:waiting_for_confirm")
async def comment_and_finish(msg: types.Message | types.CallbackQuery, state: FSMContext):
    """
    Add comment to payment and save payment to storage. Render interface for confirmation

    :param msg: Message or Callback
    :param state: redis storage
    :return: None
    """

    comment_msg = msg.message if isinstance(msg, types.CallbackQuery) else msg

    if comment_msg.text.startswith("/") or BOT_NAME in comment_msg.text:
        message = "No commands, finish process first"
        await msg.answer(message)
        return
    user_state_data = await state.get_data()
    payment_comment = msg.text if isinstance(msg, types.Message) else ""
    payment = {
        "id": str(uuid.uuid4()),
        "payer": user_state_data["payer"],
        "amount": user_state_data["payment_amount"],
        "debtors": user_state_data["debtors"],
        "comment": payment_comment,
        "date": datetime.datetime.now().strftime("%d.%m.%Y - %H:%M")
    }
    await state.update_data(final_payment=payment)
    msg_txt, keyboard = create_confirmation_keyboard(payment=payment)
    if isinstance(msg, types.Message):
        await msg.answer(text=msg_txt, reply_markup=keyboard)
    else:
        await msg.message.edit_text(text=msg_txt, reply_markup=keyboard)
    await AddPayment.waiting_for_confirm.set()


async def confirm_payment(msg: types.CallbackQuery, state: FSMContext):
    """
    After payment confirmation save it to Redis and DB. Clear temp storage.

    :param msg: Callback
    :param state: redis storage
    :return: None
    """

    chat_id = str(msg.message.chat.id)
    user_state_data = await state.get_data()
    group_name = RDS.get_chat_debts_group_name(chat_id=chat_id)
    DB.add_chat_group_payment(chat_id=chat_id, group_name=group_name, payment=user_state_data["final_payment"])
    RDS.add_chat_payment_update_balances(chat_id=chat_id, payment=user_state_data["final_payment"])
    message = "Payment added"
    await msg.message.answer(message)
    await msg.answer()
    await state.finish()


@timeout(state_to_cancel="AddPayment:finish_all")
async def end_counting(msg: types.Message, state: FSMContext):
    """
    Finish all payments, transform all balances to money transfers. Add keyboard with cancel and pay buttons -
    either pay all and zero balances or continue payments add

    :param msg: Message
    :param state: redis storage
    """

    transfers = balances_to_transfers(balances=RDS.get_chat_balances(chat_id=msg.chat.id))
    await state.update_data(transfers=transfers)
    if len(transfers) == 0:
        transfers_message = "No money transfers needed"
    else:
        transfers_message = "To pay all debts:\n\n"
    transfers_message += "\n\n".join(f"{t['from']} pays {t['payment']} to {t['to']}" for t in transfers)
    await msg.answer(text=transfers_message, reply_markup=create_debts_payments_confirmation_keyboard())
    await AddPayment.finish_all.set()


async def all_debts_payed_callback(msg: types.CallbackQuery, state: FSMContext):
    """
    If user chose pay all - add every transfer to DB as a single payment (balances - zero)
    :param msg: Callback
    :param state: redis storage
    """

    chat_id = str(msg.message.chat.id)
    user_state_data = await state.get_data()
    group_name = RDS.get_chat_debts_group_name(chat_id=chat_id)
    for transfer in user_state_data["transfers"]:
        payment = {
            "payer": transfer["from"],
            "amount": transfer["payment"],
            "debtors": [transfer["to"]],
            "comment": "Debt payback",
            "date": datetime.datetime.now().strftime("%d.%m.%Y - %H:%M")
        }
        DB.add_chat_group_payment(chat_id=chat_id, group_name=group_name, payment=payment)
        RDS.add_chat_payment_update_balances(chat_id=chat_id, payment=payment)

    message = "All debts payed, payments written to history"
    await msg.message.answer(message)
    await msg.answer()
    await state.finish()


def register_payment_handlers(dp: Dispatcher):
    # Commands handlers
    dp.register_message_handler(register_payment, chat_type=types.ChatType.GROUP, commands="pay")
    dp.register_message_handler(end_counting, chat_type=types.ChatType.GROUP, commands="end")

    # Text messages handlers
    dp.register_message_handler(get_payment_amount, chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_sum)
    dp.register_message_handler(comment_and_finish, chat_type=types.ChatType.GROUP,
                                state=AddPayment.waiting_for_comment)

    # Return to payer choosing callback
    dp.register_callback_query_handler(
        register_payment, Text("back"), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_debtors
    )

    # DEBTORS direct callback and back button callback to return
    dp.register_callback_query_handler(
        payer_select_callback, payer_cb.filter(), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_payer
    )
    dp.register_callback_query_handler(
        payer_select_callback, back_pay.filter(), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_sum
    )

    # Single or all debtors choosing callback
    dp.register_callback_query_handler(
        get_debtors_callback, debtor_cb.filter(), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_debtors
    )
    dp.register_callback_query_handler(
        get_debtors_callback, all_cb.filter(), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_debtors
    )

    # Finish debtors choose, go to payment amount input
    dp.register_callback_query_handler(
        done_select_callback, Text("done_debtors"), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_debtors
    )
    dp.register_callback_query_handler(
        done_select_callback, Text("back_sum"), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_comment
    )

    # Comments callback
    dp.register_callback_query_handler(
        comment_and_finish, Text("finish"), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_comment
    )

    # Confirmation callback
    dp.register_callback_query_handler(
        confirm_payment, Text("confirm"), chat_type=types.ChatType.GROUP, state=AddPayment.waiting_for_confirm
    )

    # All debts payback callback
    dp.register_callback_query_handler(
        all_debts_payed_callback, Text("payed_all"), chat_type=types.ChatType.GROUP, state=AddPayment.finish_all
    )
