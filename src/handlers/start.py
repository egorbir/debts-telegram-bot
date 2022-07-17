import random
from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from ..data.config import *
from ..data.db_interface import DBInterface, Core

# DB = DBInterface(
#     user=DB_USER,
#     password=DB_PASSWORD,
#     database=DB_NAME,
#     host=DB_HOST,
#     port=DB_PORT
# )
#
# CORE = Core(db=DB)
from ..utils.transfering_depts import add_person, add_payment, balances_to_payments

db_balances = {
    '@EgorBir': 0,
    '@BirYo': 0,
    '@egorbir_bg': 0
}

db_payments = dict()
db_selected_debtors = list()

db_payer = []

payer_cb = CallbackData('payer', 'msg_id', 'payer')
debtor_cb = CallbackData('debtor', 'msg_id', 'debtor')


async def send_wellcome(msg: types.Message):
    hello_message = 'This is bot for counting group debts\nTo enter the group use the /reg command'
    await msg.answer(text=hello_message)


async def register_person(msg: types.Message):
    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'
    if username in db_balances:
        message = 'Already in group'
    else:
        add_person(balances=db_balances, name=username)
        message = f'Good, now you are in group - {username}'
    await msg.answer(text=message)


async def register_payment(msg: types.Message):
    buttons = list()
    for user in db_balances:
        buttons.append(InlineKeyboardButton(
            user,
            callback_data=payer_cb.new(msg_id=msg.message_id, payer=user)
        ))
    keyboard = InlineKeyboardMarkup().add(*buttons)
    message = 'Выбери, кто платил'
    await msg.answer(reply_markup=keyboard, text=message)


async def get_payer_callback(call: types.CallbackQuery, callback_data: dict):
    if db_payer:
        db_payer[0] = callback_data['payer']
    else:
        db_payer.append(callback_data['payer'])
    buttons = [InlineKeyboardButton('All', callback_data='all_debtors')]
    for user in db_balances:
        buttons.append(
            InlineKeyboardButton(user, callback_data=debtor_cb.new(msg_id=call.message.message_id, debtor=user))
        )
    buttons.append(InlineKeyboardButton('Done', callback_data='done_debtors'))
    keyboard = InlineKeyboardMarkup().add(*buttons)
    message = 'Выбери, за кого платил'
    await call.message.edit_text(text=message, reply_markup=keyboard)


async def get_debtors_callback(call: types.CallbackQuery, callback_data: dict):
    buttons = [InlineKeyboardButton('All', callback_data='all_debtors')]
    if callback_data['debtor'] not in db_selected_debtors:
        db_selected_debtors.append(callback_data['debtor'])
    else:
        db_selected_debtors.remove(callback_data['debtor'])
    for user in db_balances:
        if user in db_selected_debtors:
            btn_txt = f'+ {user}'
        else:
            btn_txt = user

        buttons.append(
            InlineKeyboardButton(btn_txt, callback_data=debtor_cb.new(msg_id=call.message.message_id, debtor=user))
        )
    buttons.append(InlineKeyboardButton('Done', callback_data='done_debtors'))
    keyboard = InlineKeyboardMarkup().add(*buttons)
    message = 'Выбери, за кого платил'
    await call.message.edit_text(text=message, reply_markup=keyboard)


async def select_all_debtors(call: types.CallbackQuery):
    for user in db_balances:
        if user not in db_selected_debtors:
            db_selected_debtors.append(user)
    buttons = [InlineKeyboardButton('All', callback_data='all_debtors')]
    for user in db_balances:
        buttons.append(
            InlineKeyboardButton(f'+ {user}', callback_data=debtor_cb.new(msg_id=call.message.message_id, debtor=user))
        )
    buttons.append(InlineKeyboardButton('Done', callback_data='done_debtors'))
    keyboard = InlineKeyboardMarkup().add(*buttons)
    message = 'Выбери, за кого платил'
    await call.message.edit_text(text=message, reply_markup=keyboard)


async def finish_payment_add_callback(call: types.CallbackQuery):
    payment_sum = random.randint(100, 1000)
    add_payment(payment={
        'payer': db_payer[0],
        'sum': payment_sum,
        'debtors': db_selected_debtors
    }, balances_to_add=db_balances)
    db_payer.clear()
    db_selected_debtors.clear()
    await call.answer('Payment added')


async def end_counting(msg: types.Message):
    end_message = 'End counting, print all debts'
    payments = balances_to_payments(balances=db_balances)
    await msg.answer(text=payments.__str__())


async def get_help(msg: types.Message):
    help_message = 'This later will be a long help message about this bot'
    await msg.answer(text=help_message)


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(send_wellcome, CommandStart())
    dp.register_message_handler(register_person, commands='reg')
    dp.register_message_handler(register_payment, commands='pay')
    dp.register_message_handler(end_counting, commands='end')
    dp.register_message_handler(get_help, commands='help')

    dp.register_callback_query_handler(get_payer_callback, payer_cb.filter())
    dp.register_callback_query_handler(get_debtors_callback, debtor_cb.filter())
    dp.register_callback_query_handler(select_all_debtors, lambda c: c.data.startswith('all'))
    dp.register_callback_query_handler(finish_payment_add_callback, lambda c: c.data.startswith('done'))
