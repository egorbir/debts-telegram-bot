import copy
import re

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
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
from ..utils.transferring_debts import add_payment, balances_to_payments

db_balances = {
    '@EgorBir': 0,
    '@BirYo': 0,
    '@egorbir_bg': 0
}

db_payments = list()  # TODO: replace with REDIS (?)

payer_cb = CallbackData('payer', 'msg_id', 'payer')
debtor_cb = CallbackData('debtor', 'msg_id', 'debtor')


class AddPayment(StatesGroup):
    waiting_for_payer = State()
    waiting_for_debtors = State()
    waiting_for_sum = State()
    waiting_for_comment = State()


async def register_person(msg: types.Message):
    # ----------------------------------------------------- TODO replace redis read
    balances = copy.deepcopy(db_balances)
    # -----------------------------------------------------
    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'

    if username in db_balances:
        message = 'Already in group'
    else:
        db_balances[username] = 0
        message = f'Good, now you are in group - {username}'
    # ----------------------------------------------------- TODO replace redis write
    # -----------------------------------------------------
    await msg.answer(text=message)


async def register_payment(msg: types.Message, state: FSMContext):
    buttons = list()
    # ----------------------------------------------------- TODO replace redis read
    balances = copy.deepcopy(db_balances)
    # -----------------------------------------------------
    for user in balances:
        buttons.append(InlineKeyboardButton(
            user,
            callback_data=payer_cb.new(msg_id=msg.message_id, payer=user)
        ))
    keyboard = InlineKeyboardMarkup().add(*buttons)
    message = 'Выбери, кто платил'
    await msg.answer(reply_markup=keyboard, text=message)
    await AddPayment.waiting_for_payer.set()


async def back_payer_callback(call: types.CallbackQuery, state: FSMContext):
    buttons = list()
    # ----------------------------------------------------- TODO replace redis read
    balances = copy.deepcopy(db_balances)
    # -----------------------------------------------------
    for user in balances:
        buttons.append(InlineKeyboardButton(
            user,
            callback_data=payer_cb.new(msg_id=call.message.message_id, payer=user)
        ))
    keyboard = InlineKeyboardMarkup().add(*buttons)
    message = 'Выбери, кто платил'
    await call.message.edit_text(reply_markup=keyboard, text=message)
    await AddPayment.waiting_for_payer.set()


async def get_payer_callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    # ----------------------------------------------------- TODO replace redis read
    balances = copy.deepcopy(db_balances)
    await state.update_data(payer=callback_data['payer'])
    await state.update_data(debtors=list())
    # ----------------------------------------------------
    user_buttons = list()
    for user in balances:
        user_buttons.append(
            InlineKeyboardButton(user, callback_data=debtor_cb.new(msg_id=call.message.message_id, debtor=user))
        )
    tech_buttons = [
        InlineKeyboardButton('\u21A9 Back', callback_data='back'),
        InlineKeyboardButton('\u2714 All', callback_data='all_debtors'),
        InlineKeyboardButton('\u274C Cancel', callback_data='cancel'),
        InlineKeyboardButton('\u2705 Done', callback_data='done_debtors')
    ]
    keyboard = InlineKeyboardMarkup(row_width=len(user_buttons)).add(*user_buttons)
    keyboard.row(*tech_buttons)

    message = 'Выбери, за кого платил'
    await call.message.edit_text(text=message, reply_markup=keyboard)
    await AddPayment.waiting_for_debtors.set()


async def get_debtors_callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    # ----------------------------------------------- TODO: redis READ
    balances = copy.deepcopy(db_balances)
    user_state_data = await state.get_data()
    # -----------------------------------------------
    user_buttons = list()
    if callback_data['debtor'] not in user_state_data['debtors']:
        user_state_data['debtors'].append(callback_data['debtor'])
    else:
        user_state_data['debtors'].remove(callback_data['debtor'])
    for user in balances:
        if user in user_state_data['debtors']:
            btn_txt = f'\u2611 {user}'
        else:
            btn_txt = user

        user_buttons.append(
            InlineKeyboardButton(btn_txt, callback_data=debtor_cb.new(msg_id=call.message.message_id, debtor=user))
        )
    tech_buttons = [
        InlineKeyboardButton('\u21A9 Back', callback_data='back'),
        InlineKeyboardButton('\u2714 All', callback_data='all_debtors'),
        InlineKeyboardButton('\u274C Cancel', callback_data='cancel'),
        InlineKeyboardButton('\u2705 Done', callback_data='done_debtors')
    ]
    keyboard = InlineKeyboardMarkup(row_width=len(user_buttons)).add(*user_buttons)
    keyboard.row(*tech_buttons)
    message = 'Выбери, за кого платил'
    await state.update_data(debtors=user_state_data['debtors'])
    await call.message.edit_text(text=message, reply_markup=keyboard)


async def select_all_debtors(call: types.CallbackQuery, state: FSMContext):
    user_state_data = await state.get_data()
    for user in db_balances:
        if user not in user_state_data['debtors']:
            user_state_data['debtors'].append(user)
    user_buttons = list()
    for user in db_balances:
        user_buttons.append(
            InlineKeyboardButton(f'\u2611 {user}', callback_data=debtor_cb.new(msg_id=call.message.message_id, debtor=user))
        )
    tech_buttons = [
        InlineKeyboardButton('\u21A9 Back', callback_data='back'),
        InlineKeyboardButton('\u2714 All', callback_data='all_debtors'),
        InlineKeyboardButton('\u274C Cancel', callback_data='cancel'),
        InlineKeyboardButton('\u2705 Done', callback_data='done_debtors')
    ]
    keyboard = InlineKeyboardMarkup(row_width=len(user_buttons)).add(*user_buttons)
    keyboard.row(*tech_buttons)
    message = 'Выбери, за кого платил'
    await state.update_data(debtors=user_state_data['debtors'])
    await call.message.edit_text(text=message, reply_markup=keyboard)


async def selection_done_callback(call: types.CallbackQuery):
    await call.message.answer('Enter sum of payment:')
    await AddPayment.waiting_for_sum.set()


async def get_payment_sum(msg: types.Message, state: FSMContext):
    pattern = r'\d+(\.\,\d*)?$'

    if re.match(pattern, str(msg.text)):
        payment_sum = round(float(msg.text.replace(',', '.')), ndigits=2)
        await state.update_data(payment_sum=payment_sum)
        await AddPayment.waiting_for_comment.set()
        buttons = [
            InlineKeyboardButton('Yes', callback_data='comment'),
            InlineKeyboardButton('No', callback_data='finish')
        ]
        keyboard = InlineKeyboardMarkup().add(*buttons)
        await msg.answer(text='Need a comment?', reply_markup=keyboard)
    else:
        await msg.answer('Payment sum is not valid. Repeat:')


async def need_payment_comment_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer('Enter comment')
    await call.bot.answer_callback_query(call.id)


async def get_payment_comment(msg: types.Message, state: FSMContext):
    user_state_data = await state.get_data()
    payment_comment = msg.text
    add_payment(payment={
        'payer': user_state_data['payer'],
        'sum': user_state_data['payment_sum'],
        'debtors': user_state_data['debtors'],
        'comment': payment_comment
    }, payments_to_add=db_payments, balances_to_add=db_balances)
    await msg.answer('Payment added')
    await state.finish()


async def finish_payment_add_callback(call: types.CallbackQuery, state: FSMContext):
    # ----------------------------------------------- TODO: redis READ
    user_state_data = await state.get_data()
    # -----------------------------------------------

    add_payment(payment={
        'payer': user_state_data['payer'],
        'sum': user_state_data['payment_sum'],
        'debtors': user_state_data['debtors'],
        'comment': ''
    }, payments_to_add=db_payments, balances_to_add=db_balances)
    await call.message.answer('Payment added')
    await state.finish()
    await call.bot.answer_callback_query(call.id)


async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Canceled')
    await state.finish()
    await call.bot.answer_callback_query(call.id)


async def end_counting(msg: types.Message):
    payments = balances_to_payments(balances=db_balances)
    await msg.answer(text=payments.__str__())


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(register_person, commands='reg', state='*')
    dp.register_message_handler(register_payment, commands='pay', state='*')
    dp.register_message_handler(end_counting, commands='end', state='*')

    dp.register_message_handler(get_payment_sum, state=AddPayment.waiting_for_sum)
    dp.register_message_handler(get_payment_comment, state=AddPayment.waiting_for_comment)

    dp.register_callback_query_handler(get_payer_callback, payer_cb.filter(), state=AddPayment.waiting_for_payer)
    dp.register_callback_query_handler(get_debtors_callback, debtor_cb.filter(), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(back_payer_callback, lambda c: c.data.startswith('back'), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(select_all_debtors, lambda c: c.data.startswith('all'), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(selection_done_callback, lambda c: c.data.startswith('done'), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(need_payment_comment_callback, lambda c: c.data.startswith('comment'), state=AddPayment.waiting_for_comment)
    dp.register_callback_query_handler(finish_payment_add_callback, lambda c: c.data.startswith('finish'), state=AddPayment.waiting_for_comment)
    dp.register_callback_query_handler(cancel_callback, lambda c: c.data.startswith('cancel'), state='*')
