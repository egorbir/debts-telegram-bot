from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.data.redis_interface import RedisInterface

RDS = RedisInterface(host='localhost', port=6379, db=0, password=None)  # TODO from .env


async def send_wellcome(msg: types.Message):
    hello_message = 'This is bot for counting group debts\nTo enter the group use the /reg command'
    RDS.initialize_chat_redis(chat_id=msg.chat.id)
    await msg.answer(text=hello_message)


async def register_user(msg: types.Message):
    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'
    redis_balances = RDS.read_chat_balances(chat_id=msg.chat.id)
    if username not in redis_balances:
        redis_balances[username] = 0
        message = f'Good, now you are in group - {username}'
    else:
        message = 'Already in group'
    await msg.answer(text=message)
    RDS.write_chat_balances(chat_id=msg.chat.id, balances=redis_balances)


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
    dp.register_message_handler(send_wellcome, commands='start', state='*')
    dp.register_message_handler(register_user, commands='reg', state='*')
    dp.register_message_handler(list_users, commands='list', state='*')
    dp.register_message_handler(get_help, commands='help', state='*')
    dp.register_message_handler(cancel_command, commands='cancel', state='*')

    dp.register_callback_query_handler(cancel_callback, Text('cancel'), state='*')
