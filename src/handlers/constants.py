from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.callback_data import CallbackData

payer_cb = CallbackData('payer', 'payer')
debtor_cb = CallbackData('debtor', 'debtor')
all_cb = CallbackData('all', 'all')
back_pay = CallbackData('back_payers')


class AddPayment(StatesGroup):
    waiting_for_payer = State()
    waiting_for_debtors = State()
    waiting_for_sum = State()
    waiting_for_comment = State()
    waiting_for_confirm = State()