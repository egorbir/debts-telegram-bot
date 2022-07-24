from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.handlers.constants import DB, RDS


async def status(msg: types.Message):
    current_group = RDS.read_chat_debts_group_name(chat_id=msg.chat.id)
    db_groups = DB.get_chat_groups(chat_id=str(msg.chat.id))
    if current_group is None:
        if db_groups is not None:
            status_msg = 'There is no group in progress, that could happen because of server shutdown\n' \
                         'You can continue old group by command /restart'
        else:
            status_msg = 'You have not started any debts group yet. Do it with /start command'
    else:
        status_msg = f'Current group - {current_group}, calculation is in progress'
    await msg.answer(status_msg)


async def list_users(msg: types.Message):
    balances = RDS.read_chat_balances(msg.chat.id)
    result_message_text = 'No one is in debts group' if len(balances) == 0 else 'Now in the debts counting are:\n'
    for user in balances:
        result_message_text += f'{user}\n'
    await msg.answer(result_message_text)


async def get_help(msg: types.Message):
    help_message = 'This later will be a long help message about this bot'
    await msg.answer(text=help_message)


async def cancel_command(msg: types.Message, state: FSMContext):
    await msg.answer(text='Canceled')
    await state.finish()


async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Canceled')
    await state.finish()
    await call.bot.answer_callback_query(call.id)


def register_common_handlers(dp: Dispatcher):
    dp.register_message_handler(status, commands='status')
    dp.register_message_handler(list_users, commands='list')
    dp.register_message_handler(get_help, commands='help')
    dp.register_message_handler(cancel_command, commands='cancel', state='*')

    dp.register_callback_query_handler(cancel_callback, Text('cancel'), state='*')
