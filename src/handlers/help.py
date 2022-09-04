from typing import Union

from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from src.handlers.utils import EMOJIS


async def first_help_message(msg: Union[types.Message, types.CallbackQuery]):
    message = 'Данный бот предназначен для упрощения расчетов при совместных тратах в поездках, на мероприятиях и ' \
              'т.д. позволяет не считать каждый раз, кто, кому и сколько должен, а также избавляет от необходимости ' \
              'переводить деньги каждый раз после каждой траты.\n\nИспользовать просто - добавить в чат, ' \
              'зарегистрироваться и начать добавлять платежи. В конце бот сам подсчитатет и выведет, кто, кому и ' \
              'сколько дожен перевести, чтобы погасить долги. Он учтет ситуации с "круговым" долгом ' \
              '(напр. Иван -> Петр -> Андрей) и сократит кол-во переводимых денег по максимуму, минуя ' \
              'промежуточных людей.'
    buttons = [
        InlineKeyboardButton(EMOJIS['forward'], callback_data='second_help')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    if isinstance(msg, types.Message):
        await msg.answer(text=message, reply_markup=keyboard)
    elif isinstance(msg, types.CallbackQuery):
        await msg.message.edit_text(text=message, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def second_help_message(call: types.CallbackQuery):
    message = 'В контексте описания работы бота будут использоваться термины:\n\n' \
              '\u2022 <b>Чат</b> - групповой чат, в который бот добавлен администратором\n' \
              '\u2022 <b>Группа</b> - отдельная по смыслу группа трат (напр. поездка в горы, шашлыки, дача и т.д)\n' \
              '\u2022 <b>Баланс</b> - общий баланс трат пользователя\n' \
              '\u2022 <b>Положительный</b> - пользователю должны денег, ' \
              '<b>отрицательный</b> - пользователь должен денег\n' \
              '\u2022 <b>Платеж</b> - одна общая трата в рамках группы, разделенная на несколько человек. ' \
              'Каждый платеж изменяет баланс его участников\n' \
              '\u2022 <b>Регистрация</b>  - добавления юзера в группу\n'
    buttons = [
        InlineKeyboardButton(EMOJIS['backward'], callback_data='first_help'),
        InlineKeyboardButton(EMOJIS['forward'], callback_data='third_help')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await call.message.edit_text(text=message, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def third_help_message(call: types.CallbackQuery):
    message = 'Бот будет стремиться преобразовать балансы пользователей в конечные долги таким образом чтобы:\n\n' \
              '1. Сократить кол-во переводов денег между пользователями' \
              '(если А должен Б, Б должен В, то А может перевести сразу В)\n' \
              '2. Уменьшить переводимые суммы денег\n\n' \
              'Конечным результатом будет то, что каждый пользователь либо получает, либо переводит деньги в рамках ' \
              'погашения долгов'
    buttons = [
        InlineKeyboardButton(EMOJIS['backward'], callback_data='second_help'),
        InlineKeyboardButton(EMOJIS['done'], callback_data='finish_help')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await call.message.edit_text(text=message, reply_markup=keyboard)


async def finish_help(call: types.CallbackQuery):
    message = 'Чтобы увидеть эту справку снова используй команду /help'
    await call.message.edit_text(text=message)


def register_help_handlers(dp: Dispatcher):
    dp.register_message_handler(first_help_message, commands='help')

    dp.register_callback_query_handler(first_help_message, Text('first_help'))
    dp.register_callback_query_handler(second_help_message, Text('second_help'))
    dp.register_callback_query_handler(third_help_message, Text('third_help'))
    dp.register_callback_query_handler(finish_help, Text('finish_help'))
