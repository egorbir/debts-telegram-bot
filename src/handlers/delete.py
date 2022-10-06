from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.handlers.constants import DB, DeletePayment, RDS, delete_cb
from src.handlers.utils import create_found_payments_keyboard
from src.utils.transferring_debts import delete_payment


async def start_payment_delete(msg: types.Message):
    chat_id = str(msg.chat.id)
    group_name = RDS.read_chat_debts_group_name(chat_id=chat_id)
    payments = DB.get_chat_group_payments(chat_id=chat_id, group_name=group_name)['payments']
    if len(payments) == 0:
        message = 'No payments yet'
        message = 'Платежей еще не было'
        await msg.answer(message)
    else:
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton('Да', callback_data='delete_history_yes'),
            InlineKeyboardButton('Нет', callback_data='delete_history_no')
        ])
        await msg.answer('Поиск по транзакциям по комментарию. Отобразить историю?', reply_markup=keyboard)
        await DeletePayment.waiting_for_history_choose.set()


async def show_payment_history_for_delete(call: types.CallbackQuery):
    chat_id = str(call.message.chat.id)
    group_name = RDS.read_chat_debts_group_name(chat_id=chat_id)
    payments = DB.get_chat_group_payments(chat_id=chat_id, group_name=group_name)['payments']
    history_reply_template = 'История:\n'
    for p in payments:
        history_reply_template += f'\n{p["date"]} - Платил: {p["payer"]} за {", ".join(p["debtors"])} - {p["sum"]}' \
                                  f'\nКомментарий - {p["comment"]}' \
                                  f'\n____________________________'
    await call.message.edit_text(history_reply_template)
    await call.message.answer('Введите комментарий для поиска')
    await DeletePayment.waiting_for_comment.set()
    await call.answer()


async def start_search_enter_without_history(call: types.CallbackQuery):
    await call.message.edit_text('Введите комментарий для поиска')
    await DeletePayment.waiting_for_comment.set()
    await call.answer()


async def comment_search_enter(msg: types.Message, state: FSMContext):
    chat_id = str(msg.chat.id)
    group_name = RDS.read_chat_debts_group_name(chat_id=chat_id)
    payments = DB.get_chat_group_payments(chat_id=chat_id, group_name=group_name)['payments']
    matching = [p for p in payments if msg.text in p['comment'].lower()]
    search_reply_template = 'Найдено:\n'
    for i, p in enumerate(matching):
        search_reply_template += f'<b>{i+1}</b>. {p["date"]} - Платил: {p["payer"]} за {", ".join(p["debtors"])} - ' \
                                 f'{p["sum"]} \nКомментарий - {p["comment"]}' \
                                 f'\n____________________________\n'
    if len(matching) == 0:
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton('Ввести другой комментарий', callback_data='restart_search'),
            InlineKeyboardButton('Отмена', callback_data='cancel')
        ])
        await msg.answer('Ничего не найдено!', reply_markup=keyboard)
    elif len(matching) == 1:
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton('Yes', callback_data=delete_cb.new(payment=matching[0]['id'])),
            InlineKeyboardButton('Cancel', callback_data='cancel')
        ])
        message = f'Найдена одна транзакция\n\n' \
                  f'{matching[0]["date"]} - Платил: {matching[0]["payer"]} за {", ".join(matching[0]["debtors"])} - ' \
                  f'{matching[0]["sum"]} \nКомментарий - {matching[0]["comment"]} \n\n' \
                  f'Удалить?'
        await msg.answer(message, reply_markup=keyboard)
        await DeletePayment.waiting_for_confirm.set()
    else:
        await state.update_data(found_payments=matching)
        await msg.answer(f'Найдено {len(matching)} подходящих транзакций')
        await msg.answer(search_reply_template, parse_mode=types.ParseMode.HTML)
        keyboard = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton('Да', callback_data='yes_new_search'),
            InlineKeyboardButton('Нет', callback_data='no_new_search')
        ])
        await msg.answer('Уточнить поиск?', reply_markup=keyboard)
        await DeletePayment.waiting_for_search_restart.set()


async def select_payment_from_found(call: types.CallbackQuery, state: FSMContext):
    user_state_data = await state.get_data()
    await call.message.edit_text(
        text='Выбери номер нужной',
        reply_markup=create_found_payments_keyboard(found_payments=user_state_data['found_payments'])
    )
    await DeletePayment.waiting_choose_number.set()
    await call.answer()


async def delete_selected_payment(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    chat_id = str(call.message.chat.id)
    payment = RDS.get_payment(chat_id=call.message.chat.id, payment_id=callback_data['payment'])
    DB.delete_chat_group_payment(
        chat_id=chat_id,
        group_name=RDS.read_chat_debts_group_name(chat_id=chat_id),
        payment=payment
    )
    delete_payment(payment=payment, chat_id=call.message.chat.id, redis=RDS)
    await call.message.edit_text(f'Платеж удален!')
    await state.finish()


def register_delete_handlers(dp: Dispatcher):
    dp.register_message_handler(
        start_payment_delete, chat_type=types.ChatType.GROUP, commands='delete', state='*'
    )
    dp.register_callback_query_handler(
        show_payment_history_for_delete, Text('delete_history_yes'), chat_type=types.ChatType.GROUP,
        state=DeletePayment.waiting_for_history_choose
    )
    dp.register_callback_query_handler(
        start_search_enter_without_history, Text('delete_history_no'), chat_type=types.ChatType.GROUP,
        state=DeletePayment.waiting_for_history_choose
    )
    dp.register_callback_query_handler(
        start_search_enter_without_history, Text('restart_search'), chat_type=types.ChatType.GROUP,
        state=DeletePayment.waiting_for_comment
    )
    dp.register_message_handler(
        comment_search_enter, state=DeletePayment.waiting_for_comment, chat_type=types.ChatType.GROUP
    )
    dp.register_callback_query_handler(
        select_payment_from_found, Text('no_new_search'), state=DeletePayment.waiting_for_search_restart,
        chat_type=types.ChatType.GROUP
    )
    dp.register_callback_query_handler(
        start_search_enter_without_history, Text('yes_new_search'), state=DeletePayment.waiting_for_search_restart,
        chat_type=types.ChatType.GROUP
    )

    dp.register_callback_query_handler(
        delete_selected_payment, delete_cb.filter(),
        state=[DeletePayment.waiting_choose_number, DeletePayment.waiting_for_confirm],
        chat_type=types.ChatType.GROUP
    )
