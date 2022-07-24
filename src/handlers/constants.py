from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from src.data.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from src.data.db_interface import DBInterface
from src.data.redis_interface import RedisInterface

DB = DBInterface(
    user=DB_USER,
    password=DB_PASSWORD,
    database_name=DB_NAME,
    host=DB_HOST,
    port=DB_PORT
)

RDS = RedisInterface(host='localhost', port=6379, db=0, password=None)  # TODO from .env


payer_cb = CallbackData('payer', 'payer')
debtor_cb = CallbackData('debtor', 'debtor')
all_cb = CallbackData('all', 'all')
back_pay = CallbackData('back_payers')


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
    finish_all = State()
