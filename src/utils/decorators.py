import asyncio
import functools

from aiogram import types
from aiogram.dispatcher import FSMContext


def timeout(state_to_cancel: str):
    """
    Timeout decorator. Finishes dialog and resets state f user hasn't performed any action and bot state hasn't changed
    Resets if state is still state_to_cancel after 300 secs timeout
    :param state_to_cancel: state to check after timeout if it's still the same
    """

    def timeout_wrapper(handler_func):
        @functools.wraps(handler_func)
        async def wrapper(
                msg: types.Message | types.CallbackQuery,
                state: FSMContext,
                callback_data: dict | None = None
        ):
            timeout_message = "Waiting for response message timed out. " \
                              "Start the operation again by running the same command"
            if callback_data is not None:
                await handler_func(msg, state, callback_data)
            else:
                await handler_func(msg, state)
            await asyncio.sleep(300)
            if await state.get_state() == state_to_cancel:
                if isinstance(msg, types.Message):
                    await msg.reply(timeout_message)
                elif isinstance(msg, types.CallbackQuery):
                    await msg.message.reply(timeout_message)
                await state.finish()
        return wrapper
    return timeout_wrapper
