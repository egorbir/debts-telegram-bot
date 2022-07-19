from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext


async def send_wellcome(msg: types.Message):
    hello_message = 'This is bot for counting group debts\nTo enter the group use the /reg command'
    await msg.answer(text=hello_message)


async def get_help(msg: types.Message):
    help_message = 'This later will be a long help message about this bot'
    await msg.answer(text=help_message)


async def cancel_command(msg: types.Message, state: FSMContext):
    await msg.answer(text='Canceled')
    await state.finish()


def register_common_handlers(dp: Dispatcher):
    dp.register_message_handler(send_wellcome, commands='start', state='*')
    dp.register_message_handler(get_help, commands='help', state='*')
    dp.register_message_handler(cancel_command, commands='cancel', state='*')
