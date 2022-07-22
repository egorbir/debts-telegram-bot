from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.data.redis_interface import RedisInterface
from src.handlers.constants import Register

RDS = RedisInterface(host='localhost', port=6379, db=0, password=None)  # TODO from .env


async def send_wellcome(msg: types.Message):
    if RDS.read_chat_debts_group_name(chat_id=msg.chat.id) is not None:
        await msg.answer('Group is already registered, you can only /restart to create a new one')
    else:
        hello_message = 'This is bot for counting group debts\nTo start counting enter short group name (ex. the ' \
                        'name of an event or the country/city of a trip etc.)\nBe careful, this name cannot be ' \
                        'edited, only restart'
        await msg.answer(text=hello_message)
        await Register.waiting_for_group_name.set()


async def get_group_name(msg: types.Message, state: FSMContext):
    group_name = msg.text.strip().replace(' ', '_')
    RDS.initialize_chat_redis(chat_id=msg.chat.id, group_name=group_name)
    user_registration_msg = 'Your group started! Now everyone who is in this group please tap the command /reg\n' \
                            'To exit group use /unreg (you can exit only if there are no payments yet)'
    await msg.answer('Your group started! Now everyone who is in this group please tap the command /reg')
    await state.finish()


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


async def unregister_user(msg: types.Message):
    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'
    balances = RDS.read_chat_balances(chat_id=msg.chat.id)
    if len(RDS.read_chat_payments(chat_id=msg.chat.id)) == 0:
        balances.pop(username, None)
        result_msg = f'User {username} successfully deleted from group'
        RDS.write_chat_balances(chat_id=msg.chat.id, balances=balances)
    else:
        result_msg = 'There are already payments in this group, ypu cannot leave'
    await msg.answer(result_msg)


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
    dp.register_message_handler(get_group_name, state=Register.waiting_for_group_name)
    dp.register_message_handler(register_user, commands='reg', state='*')
    dp.register_message_handler(unregister_user, commands='unreg', state='*')
    dp.register_message_handler(list_users, commands='list', state='*')
    dp.register_message_handler(get_help, commands='help', state='*')
    dp.register_message_handler(cancel_command, commands='cancel', state='*')

    dp.register_callback_query_handler(cancel_callback, Text('cancel'), state='*')
