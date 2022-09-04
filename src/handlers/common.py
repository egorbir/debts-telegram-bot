from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.handlers.constants import DB, RDS


async def status(msg: types.Message):
    """
    Status command. Checks database and redis and prints current status of what is going on
    """

    current_group = RDS.read_chat_debts_group_name(chat_id=msg.chat.id)
    db_groups = DB.get_chat_groups(chat_id=str(msg.chat.id))
    if current_group is None:
        if db_groups is not None:
            status_msg = 'There is no group in progress, that could happen because of server shutdown\n' \
                         'You can continue old group by command /restart'
            status_msg = 'Сейчас никакие расчеты не ведутся, это могло произойти из-за перезагрузки сервера.\n' \
                         'Старую группу можно продолжить при помощи команды /restart'
        else:
            status_msg = 'You have not started any debts group yet. Do it with /start command'
            status_msg = 'Вы еще не создали ни одной группы. Используйте /start'
    else:
        status_msg = f'Current group - {current_group}, calculation is in progress'
        status_msg = f'Текущая группа - {current_group}, расчеты в процессе'
    await msg.answer(status_msg)


async def list_users(msg: types.Message):
    """
    Prints all users who registered for current group of debts with /reg command
    """

    balances = RDS.read_chat_balances(msg.chat.id)
    result_message_text = 'No one is in debts group' if len(balances) == 0 else 'Now in the debts counting are:\n'
    result_message_text = 'В группе никто не зарегистрирован' if len(balances) == 0 else 'Сейчас в группе:\n'
    for user in balances:
        result_message_text += f'{user}\n'
    await msg.answer(result_message_text)


async def cancel_command(msg: types.Message, state: FSMContext):
    """
    Cancels any action that is in progress and finishes FSM state
    """

    message = 'Canceled'
    message = 'Отменено'
    await msg.answer(text=message)
    await state.finish()


async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    """
    Callback to cancel any action and finish FSM state
    """

    message = 'Canceled'
    message = 'Отменено'
    await call.message.answer(text=message)
    await state.finish()
    await call.bot.answer_callback_query(call.id)


def register_common_handlers(dp: Dispatcher):
    dp.register_message_handler(status, commands='status')
    dp.register_message_handler(list_users, commands='list')
    dp.register_message_handler(cancel_command, commands='cancel', state='*')

    dp.register_callback_query_handler(cancel_callback, Text('cancel'), state='*')
