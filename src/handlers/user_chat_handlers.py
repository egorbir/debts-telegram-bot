import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from src.handlers.constants import Feedback
from src.handlers.utils import timeout


@timeout(state_to_cancel='Feedback:waiting_for_feedback_message')
async def feedback(msg: types.Message, state: FSMContext):
    message = 'Спасибо за использование бота! \nЕсли есть замечания по работе, предложения по улучшению или просто ' \
              'отзыв, можно написать его следующим сообщением'
    await msg.answer(message)
    await Feedback.waiting_for_feedback_message.set()


async def get_user_feedback(msg: types.Message, state: FSMContext):
    user_full_name = msg.from_user.full_name
    username = msg.from_user.username
    user_feedback = msg.text
    feedback_message = f'Пользователь: {user_full_name}, ID: @{username} написал: \n{user_feedback}'
    await msg.answer('Спасибо за оставленный фидбэк!')
    await msg.bot.send_message(chat_id=68270902, text=feedback_message)
    await state.finish()


def register_user_chat_handlers(dp: Dispatcher):
    dp.register_message_handler(feedback, commands='feedback', state='*', chat_type=types.ChatType.PRIVATE)
    dp.register_message_handler(
        get_user_feedback, state=Feedback.waiting_for_feedback_message, chat_type=types.ChatType.PRIVATE
    )
