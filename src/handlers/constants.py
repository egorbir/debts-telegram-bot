from aiogram import types
from aiogram.dispatcher.filters import Filter
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.callback_data import CallbackData

payer_cb = CallbackData('payer', 'payer')
debtor_cb = CallbackData('debtor', 'debtor')
all_cb = CallbackData('all', 'all')
back_pay = CallbackData('back_payers')


class NotCommandFilter(Filter):
    key = 'not command'

    async def check(self, msg: types.Message) -> bool:
        return not msg.text.startswith('/') and '@RepetitionsBot' not in msg.text


class Register(StatesGroup):
    initial_startup = State()
    waiting_for_group_name = State()
    waiting_for_restart_group_name = State()


class AddPayment(StatesGroup):
    waiting_for_payer = State()
    waiting_for_debtors = State()
    waiting_for_sum = State()
    waiting_for_comment = State()
    waiting_for_confirm = State()
