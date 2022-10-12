from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from src.utils.decorators import timeout
from src.utils.state_groups import Feedback


@timeout(state_to_cancel="Feedback:waiting_for_feedback_message")
async def feedback(msg: types.Message, state: FSMContext):
    """
    Handle user feedback in user personal chat
    """

    message = "Thanks for using the bot! \nIf you have any comments on the work, suggestions for improvement, or " \
              "just feedback, you can write it in the following message"
    await msg.answer(message)
    await Feedback.waiting_for_feedback_message.set()


async def get_user_feedback(msg: types.Message, state: FSMContext):
    """
    Send user feedback to the admin
    """

    user_full_name = msg.from_user.full_name
    username = msg.from_user.username
    user_feedback = msg.text
    feedback_message = f"User: {user_full_name}, ID: @{username} wrote: \n{user_feedback}"
    await msg.answer("Thank you for leaving feedback!")
    await msg.bot.send_message(chat_id=68270902, text=feedback_message)  # TODO admin ID from constants
    await state.finish()


def register_user_chat_handlers(dp: Dispatcher):
    dp.register_message_handler(feedback, commands="feedback", state="*", chat_type=types.ChatType.PRIVATE)
    dp.register_message_handler(
        get_user_feedback, state=Feedback.waiting_for_feedback_message, chat_type=types.ChatType.PRIVATE
    )
