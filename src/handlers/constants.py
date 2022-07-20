from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.callback_data import CallbackData

payer_cb = CallbackData('payer', 'msg_id', 'payer')
debtor_cb = CallbackData('debtor', 'msg_id', 'debtor')


class AddPayment(StatesGroup):
    waiting_for_payer = State()
    waiting_for_debtors = State()
    waiting_for_sum = State()
    waiting_for_comment = State()
