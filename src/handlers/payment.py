import datetime
import re
from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .constants import AddPayment, DB, RDS, all_cb, back_pay, debtor_cb, payer_cb
from .utils import EMOJIS, create_comment_keyboard, create_confirmation_keyboard, create_debtors_keyboard, \
    create_debts_payments_confirmation_keyboard, create_payers_keyboard, edit_user_state_for_debtors
from ..data.config import BOT_NAME
from ..utils.transferring_debts import add_payment, balances_to_transfers


async def register_payment(msg: Union[types.Message, types.CallbackQuery]):
    """
    Base start of payment add handler.
    Start of add - command '/pay', come back from payer - callback 'back'

    :param msg: either Message or Callback
    :return: None
    """

    # Multipurpose handler for both '/pay' command and 'back' inline button
    chat_id = msg.chat.id if isinstance(msg, types.Message) else msg.message.chat.id
    balances = RDS.read_chat_balances(chat_id=chat_id)
    if len(balances) < 3:
        await msg.answer(f'Works with 3 or more people, now - {len(balances)}. '
                         f'Use /reg command and check who is in group with /list')
        return
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
    """
    Callback after payer choose.
    First - save selected payer to user storage. Second - render interface for debtors choose

    :param call: Callback
    :param callback_data: Callback data
    :param state: redis state
    :return: None
    """

    # Save selected payer to storage
    balances = RDS.read_chat_balances(chat_id=call.message.chat.id)
    await state.update_data(debtors=list())
    if 'payer' in callback_data:
        await state.update_data(payer=callback_data['payer'])

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
    """
    Callback for debtors choose. Render who are chosen or not. Save chosen to storage
    Starts on: 1 - initial render, 2 - single debtor change, 3 - select all debtors

    :param call: Callback
    :param callback_data: Callback data
    :param state: redis state
    :return: None
    """

    balances = RDS.read_chat_balances(chat_id=call.message.chat.id)
    user_state_data = await state.get_data()
    user_state_data['debtors'] = edit_user_state_for_debtors(
        debtors_state=user_state_data['debtors'],
        callback_data=callback_data,
        balances_users=list(balances.keys())
    )
    message = 'Выбери, за кого платил'
    await state.update_data(debtors=user_state_data['debtors'])
    await call.message.edit_text(
        text=message,
        reply_markup=create_debtors_keyboard(
            balances=balances,
            selected_debtors=user_state_data['debtors']
        )
    )


async def done_select_callback(call: types.CallbackQuery, state: FSMContext):
    """
    Callback on done button after all debtors are chosen.
    Render interface for payment sum enter

    :param call: Callback
    :param state: redis state
    :return: None
    """

    user_state_data = await state.get_data()
    if len(user_state_data['debtors']) == 0:
        await call.answer('No one chosen')
    else:
        sum_message = 'Enter sum of payment:'
        keyboard = InlineKeyboardMarkup().add(
            *[
                InlineKeyboardButton(f'{EMOJIS["back"]} Back', callback_data=back_pay.new()),
                InlineKeyboardButton(f'{EMOJIS["cancel"]} Cancel', callback_data='cancel')
            ]
        )
        await call.message.edit_text(text=sum_message, reply_markup=keyboard)
        await AddPayment.waiting_for_sum.set()


async def get_payment_sum(msg: types.Message, state: FSMContext):
    """
    Recognize payment sum, save to storage. Render interface for comment input

    :param msg: Message
    :param state: redis storage
    :return: None
    """

    pattern = r'\d+(\,\d*)?$'

    if re.match(pattern, msg.text.replace('.', ',')) and float(msg.text) != 0:
        payment_sum = round(float(msg.text.replace(',', '.')), ndigits=2)
        await state.update_data(payment_sum=payment_sum)
        await AddPayment.waiting_for_comment.set()
        await msg.answer(text='Need a comment?', reply_markup=create_comment_keyboard())
    else:
        await msg.answer('Payment sum is not valid. Repeat:')


async def payment_comment_callback(call: types.CallbackQuery):
    """
    Enter comment for payment

    :param call: Callback
    :return: None
    """

    await call.message.answer('Enter comment')
    await call.bot.answer_callback_query(call.id)


async def comment_and_finish(call: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """
    Add comment to payment and save payment to storage. Render interface for confirmation

    :param call: Message or Callback
    :param state: redis storage
    :return: None
    """

    comment_msg = call.message if isinstance(call, types.CallbackQuery) else call

    if comment_msg.text.startswith('/') or BOT_NAME in comment_msg.text:
        await call.answer('No commands, finish process first')
        return
    user_state_data = await state.get_data()
    payment_comment = call.text if isinstance(call, types.Message) else ''
    payment = {
        'payer': user_state_data['payer'],
        'sum': user_state_data['payment_sum'],
        'debtors': user_state_data['debtors'],
        'comment': payment_comment,
        'date': datetime.datetime.now().strftime('%d.%m.%Y - %H:%M')
    }
    await state.update_data(final_payment=payment)
    msg_txt, keyboard = create_confirmation_keyboard(payment=payment)
    if isinstance(call, types.Message):
        await call.answer(text=msg_txt, reply_markup=keyboard)
    else:
        await call.message.edit_text(text=msg_txt, reply_markup=keyboard)
    await AddPayment.waiting_for_confirm.set()


async def confirm_payment(call: types.CallbackQuery, state: FSMContext):
    """
    After payment confirmation save it to Redis and DB. Clear temp storage.

    :param call: Callback
    :param state: redis storage
    :return: None
    """

    chat_id = str(call.message.chat.id)
    user_state_data = await state.get_data()
    add_payment(payment=user_state_data['final_payment'], chat_id=call.message.chat.id, redis=RDS)
    DB.add_chat_group_payment(
        chat_id=chat_id,
        group_name=RDS.read_chat_debts_group_name(chat_id=chat_id),
        payment=user_state_data['final_payment']
    )
    await call.message.answer('Payment added')
    await call.answer()
    await state.finish()


async def end_counting(msg: types.Message, state: FSMContext):
    """
    Finish all payments, transform all balances to money transfers. Add keyboard with cancel and pay buttons -
    either pay all and zero balances or continue payments add

    :param msg: Message
    :param state: redis storage
    """

    transfers = balances_to_transfers(chat_id=msg.chat.id, redis=RDS)
    await state.update_data(transfers=transfers)
    if len(transfers) == 0:
        transfers_message = 'No money transfers needed'
    else:
        transfers_message = 'To pay all debts:\n\n'
    transfers_message += '\n\n'.join(f'{t["from"]} pays {t["payment"]} to {t["to"]}' for t in transfers)
    await msg.answer(text=transfers_message, reply_markup=create_debts_payments_confirmation_keyboard())
    await AddPayment.finish_all.set()


async def all_debts_payed_callback(call: types.CallbackQuery, state: FSMContext):
    """
    If user chose pay all - add every transfer to DB as a single payment (balances - zero)
    :param call: Callback
    :param state: redis storage
    """

    user_state_data = await state.get_data()
    for transfer in user_state_data['transfers']:
        add_payment(payment={
            'payer': transfer['from'],
            'sum': transfer['payment'],
            'debtors': [transfer['to']],
            'comment': 'Debt payback',
            'date': datetime.datetime.now().strftime('%d.%m.%Y - %H:%M')
        }, chat_id=call.message.chat.id, redis=RDS)
    await call.message.answer('All debts payed, payments written to history')
    await call.answer()
    await state.finish()


def register_payment_handlers(dp: Dispatcher):
    # Commands handlers
    dp.register_message_handler(register_payment, commands='pay')
    dp.register_message_handler(end_counting, commands='end')

    # Text messages handlers
    dp.register_message_handler(get_payment_sum, state=AddPayment.waiting_for_sum)
    dp.register_message_handler(comment_and_finish, state=AddPayment.waiting_for_comment)

    # Return to payer choosing callback
    dp.register_callback_query_handler(register_payment, Text('back'), state=AddPayment.waiting_for_debtors)
    # DEBTORS direct callback and back button callback to return
    dp.register_callback_query_handler(payer_select_callback, payer_cb.filter(), state=AddPayment.waiting_for_payer)
    dp.register_callback_query_handler(payer_select_callback, back_pay.filter(), state=AddPayment.waiting_for_sum)
    # Single or all debtors choosing callback
    dp.register_callback_query_handler(get_debtors_callback, debtor_cb.filter(), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(get_debtors_callback, all_cb.filter(), state=AddPayment.waiting_for_debtors)
    # Finish debtors choose, go to payment sum input
    dp.register_callback_query_handler(done_select_callback, Text('done_debtors'), state=AddPayment.waiting_for_debtors)
    dp.register_callback_query_handler(done_select_callback, Text('back_sum'), state=AddPayment.waiting_for_comment)
    # Payment input
    dp.register_callback_query_handler(payment_comment_callback, Text('comment'), state=AddPayment.waiting_for_comment)
    # Comments callback
    dp.register_callback_query_handler(comment_and_finish, Text('finish'), state=AddPayment.waiting_for_comment)
    # Confirmation callback
    dp.register_callback_query_handler(confirm_payment, Text('confirm'), state=AddPayment.waiting_for_confirm)
    # All debts payback callback
    dp.register_callback_query_handler(all_debts_payed_callback, Text('payed_all'), state=AddPayment.finish_all)
