from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import CommandStart


async def send_wellcome(msg: types.Message):
    hello_message = 'This is bot for counting group depts'
    await msg.answer(text=hello_message)


async def end_counting(msg: types.Message):
    end_message = 'End counting, print all depts'
    await msg.answer(text=end_message)


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(send_wellcome, CommandStart())
    dp.register_message_handler(end_counting, commands='end')
