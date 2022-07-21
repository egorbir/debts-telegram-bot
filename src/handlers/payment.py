import datetime
import re
from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .constants import payer_cb, AddPayment, debtor_cb
from .utils import create_payers_keyboard, create_debtors_keyboard
from ..data.redis_interface import RedisInterface
from ..utils.transferring_debts import add_payment, balances_to_payments

# DB = DBInterface(
#     user=DB_USER,
#     password=DB_PASSWORD,
#     database=DB_NAME,
#     host=DB_HOST,
#     port=DB_PORT
# )
#
# CORE = Core(db=DB)

RDS = RedisInterface(host='localhost', port=6379, db=0, password=None)  # TODO from .env


async def register_payment(msg: Union[types.Message, types.CallbackQuery]):
    # Multipurpose handler for both '/pay' command and 'back' inline button
    chat_id = msg.chat.id if isinstance(msg, types.Message) else msg.message.chat.id
    balances = RDS.read_chat_balances(chat_id=chat_id)
    message = 'Выбери, кто платил'
    payers_keyboard = create_payers_keyboard(balances=balances)
    if isinstance(msg, types.Message):
        await msg.answer(
            reply_markup=payers_keyboard, text=message
        )
    else:
        await msg.message.edit_text(
            reply_markup=create_payers_keyboard(balances=balances), text=message
        )
    await AddPayment.waiting_for_payer.set()


async def payer_select_callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    # Save selected payer to storage
    balances = RDS.read_chat_balances(chat_id=call.message.chat.id)
    await state.update_data(payer=callback_data['payer'])
    await state.update_data(debtors=list())

    # Start next step rendering
    message = 'Выбери, за кого платил'
    await call.message.edit_text(
        text=message,
        reply_markup=create_debtors_keyboard(
            balances=balances,
            selected_debtors=list()
        )
    )
    await AddPayment.waiting_for_debtors.set()


async def get_debtors_callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    balances = RDS.read_chat_balances(chat_id=call.message.chat.id)
    user_state_data = await state.get_data()
    if callback_data['debtor'] not in user_state_data['debtors']:
        user_state_data['debtors'].append(callback_data['debtor'])
    else:
        user_state_data['debtors'].remove(callback_data['debtor'])
    message = 'Выбери, за кого платил'
    await state.update_data(debtors=user_state_data['debtors'])
    await call.message.edit_text(
        text=message,
        reply_markup=create_debtors_keyboard(
            balances=balances,
            selected_debtors=user_state_data['debtors']
        )
    )


async def select_all_debtors(call: types.CallbackQuery, state: FSMContext):
    balances = RDS.read_chat_balances(chat_id=call.message.chat.id)
    user_state_data = await state.get_data()
    for user in balances:
        if user not in user_state_data['debtors']:
            user_state_data['debtors'].append(user)
    message = 'Выбери, за кого платил'
    await state.update_data(debtors=user_state_data['debtors'])
    await call.message.edit_text(
        text=message,
        reply_markup=create_debtors_keyboard(
            balances=balances,
            selected_debtors=user_state_data['debtors']
        )
    )


async def done_select_callback(call: types.CallbackQuery):
    await call.message.answer('Enter sum of payment:')
    await AddPayment.waiting_for_sum.set()


async def get_payment_sum(msg: types.Message, state: FSMContext):
    pattern = r'\d+(\,\d*)?$'

    if re.match(pattern, msg.text.replace('.', ',')):
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


async def payment_comment_callback(call: types.CallbackQuery):
    await call.message.answer('Enter comment')
    await call.bot.answer_callback_query(call.id)


async def get_payment_comment(msg: types.Message, state: FSMContext):
    user_state_data = await state.get_data()
    payment_comment = msg.text
    add_payment(payment={
        'payer': user_state_data['payer'],
        'sum': user_state_data['payment_sum'],
        'debtors': user_state_data['debtors'],
        'comment': payment_comment,
        'date': datetime.datetime.now().strftime('%d.%m.%Y - %H:%M')
    }, chat_id=msg.chat.id, redis=RDS)
    await msg.answer('Payment added')
    await state.finish()


async def finish_add_pay_callback(call: types.CallbackQuery, state: FSMContext):
    user_state_data = await state.get_data()

    add_payment(payment={
        'payer': user_state_data['payer'],
        'sum': user_state_data['payment_sum'],
        'debtors': user_state_data['debtors'],
        'comment': '',
        'date': datetime.datetime.now().strftime('%d.%m.%Y - %H:%M')
    }, chat_id=call.message.chat.id, redis=RDS)
    await call.message.answer('Payment added')
    await state.finish()
    await call.bot.answer_callback_query(call.id)


async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Canceled')
    await state.finish()
    await call.bot.answer_callback_query(call.id)


async def end_counting(msg: types.Message):
    payments = balances_to_payments(chat_id=msg.chat.id, redis=RDS)
    await msg.answer(text=payments.__str__())


def register_payment_handlers(dp: Dispatcher):
    dp.register_message_handler(register_payment, commands='pay', state='*')
    dp.register_message_handler(end_counting, commands='end', state='*')

    dp.register_message_handler(get_payment_sum, state=AddPayment.waiting_for_sum)
    dp.register_message_handler(get_payment_comment, state=AddPayment.waiting_for_comment)

    dp.register_callback_query_handler(payer_select_callback, payer_cb.filter(), state=AddPayment.waiting_for_payer)
    dp.register_callback_query_handler(get_debtors_callback, debtor_cb.filter(), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(register_payment, Text('back'), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(select_all_debtors, Text('all_debtors'), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(done_select_callback, Text('done_debtors'), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(payment_comment_callback, Text('comment'), state=AddPayment.waiting_for_comment)
    dp.register_callback_query_handler(finish_add_pay_callback, Text('finish'), state=AddPayment.waiting_for_comment)
    dp.register_callback_query_handler(cancel_callback, Text('cancel'), state='*')
