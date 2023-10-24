from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from src.constants import EMOJIS


async def first_help_message(msg: types.Message | types.CallbackQuery):
    """
    Start bot help dialog
    """

    message = 'This bot is designed to simplify calculations when spending together on trips, events, etc. ' \
              'It allows you not to count every time who owes whom and how much, and also eliminates the need to ' \
              'transfer money every time after each expenditure.\n\n' \
              'It is easy to use - add to the chat, register and start adding payments. At the end, the bot itself ' \
              'will calculate and display who should transfer to whom and how much to pay off debts.' \
              'It will take into account situations with “complex” debt (for example John -> Bob -> Andrew) ' \
              'and will reduce the amount of money transferred, bypassing people in the middle'
    buttons = [
        InlineKeyboardButton(EMOJIS["forward"], callback_data="second_help")
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    if isinstance(msg, types.Message):
        await msg.answer(text=message, reply_markup=keyboard)
    elif isinstance(msg, types.CallbackQuery):
        await msg.message.edit_text(text=message, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def second_help_message(call: types.CallbackQuery):
    """
    Second message in bot help dialog 
    """

    message = "Describing how the bot works, the following terms will be used:\n\n" \
              "\u2022 <b>Chat</b> - group chat in which the bot was added as the administrator\n" \
              "\u2022 <b>Group of payments (or just group)</b> - a separate group of expenses '\
              '(for example trip to the mountains, barbecue ets.)\n" \
              "\u2022 <b>Balance</b> - total user spending balance\n" \
              "\u2022 <b>Positive</b> - the user is owed money, <b>negative</b> - user owes money\n" \
              "\u2022 <b>Payment</b> - one common expense within the group, divided among several people. " \
              "Each payment changes the balance of its participants\n" \
              "\u2022 <b>Registration</b>  - adding a user to a group\n"
    buttons = [
        InlineKeyboardButton(EMOJIS["backward"], callback_data="first_help"),
        InlineKeyboardButton(EMOJIS["forward"], callback_data="third_help")
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await call.message.edit_text(text=message, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def third_help_message(call: types.CallbackQuery):
    """
    Third message in bot help dialog
    """

    message = "The bot will try to convert user balances into final debts in such a way that:\n\n" \
              "1. Reduce the number of money transfers between users" \
              "(if John owes Bob, and Bob owes Andrew, then John can transfer to Andrew directly)\n" \
              "2. Reduce the amount of money transferred\n\n" \
              "The end result will be that each user either receives or transfers money as part of paying off debts."
    buttons = [
        InlineKeyboardButton(EMOJIS["backward"], callback_data="second_help"),
        InlineKeyboardButton(EMOJIS["done"], callback_data="finish_help")
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await call.message.edit_text(text=message, reply_markup=keyboard)


async def finish_help(call: types.CallbackQuery):
    """
    Finish hel dialog
    """

    message = "To see this help, use the command again /help"
    await call.message.edit_text(text=message)


def register_help_handlers(dp: Dispatcher):
    dp.register_message_handler(first_help_message, commands="help")

    dp.register_callback_query_handler(first_help_message, Text("first_help"))
    dp.register_callback_query_handler(second_help_message, Text("second_help"))
    dp.register_callback_query_handler(third_help_message, Text("third_help"))
    dp.register_callback_query_handler(finish_help, Text("finish_help"))
