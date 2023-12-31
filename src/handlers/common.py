from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.constants import DB, RDS


async def status(msg: types.Message):
    """
    Status command. Checks database and redis and prints current status of what is going on
    """

    current_group = RDS.get_chat_debts_group_name(chat_id=msg.chat.id)
    db_groups = DB.get_chat_groups(chat_id=str(msg.chat.id))
    if current_group is None:
        if db_groups is not None:
            status_msg = "There is no group in progress, that could happen because of server shutdown\n" \
                         "You can continue old group by command /restart"
        else:
            status_msg = "You have not started any debts group yet. Do it with /start command"
    else:
        status_msg = f"Current group - {current_group}, calculation is in progress"
    await msg.answer(status_msg)


async def list_users(msg: types.Message):
    """
    Prints all users who registered for current group of debts with /reg command
    """

    balances = RDS.get_chat_balances(msg.chat.id)
    result_message_text = "No one is in debts group" if len(balances) == 0 else "Now in the debts counting are:\n"
    for user in balances:
        result_message_text += f"{user}\n"
    await msg.answer(result_message_text)


async def cancel_command(msg: types.Message, state: FSMContext):
    """
    Cancels any action that is in progress and finishes FSM state
    """

    message = "Canceled"
    await msg.answer(text=message)
    await state.finish()


async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    """
    Callback to cancel any action and finish FSM state
    """

    message = "Canceled"
    await call.message.answer(text=message)
    await state.finish()
    await call.bot.answer_callback_query(call.id)


def register_common_handlers(dp: Dispatcher):
    dp.register_message_handler(status, commands="status", chat_type=types.ChatType.GROUP)
    dp.register_message_handler(list_users, commands="list", chat_type=types.ChatType.GROUP)
    dp.register_message_handler(cancel_command, commands="cancel", chat_type=types.ChatType.GROUP, state="*")

    dp.register_callback_query_handler(cancel_callback, Text("cancel"), chat_type=types.ChatType.GROUP, state="*")
