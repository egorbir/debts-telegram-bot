from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from src.data.credentials import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, REDIS_HOST, REDIS_PASS, REDIS_PORT
from src.data.db_interface import DBInterface
from src.data.redis_interface import RedisInterface

# Database interface instance
DB = DBInterface(
    user=DB_USER,
    password=DB_PASSWORD,
    database_name=DB_NAME,
    host=DB_HOST,
    port=DB_PORT
)

# Redis interface instance
RDS = RedisInterface(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS)


# Different callback data to use in different keyboards
payer_cb = CallbackData('payer', 'payer')
debtor_cb = CallbackData('debtor', 'debtor')
all_cb = CallbackData('all', 'all')
delete_cb = CallbackData('payment', 'payment')
back_pay = CallbackData('back_payers')


# States to use while start and registration
class Register(StatesGroup):
    initial_startup = State()
    waiting_for_group_name = State()
    waiting_for_restart_group_name = State()


# States to use in payment add process
class AddPayment(StatesGroup):
    waiting_for_payer = State()
    waiting_for_debtors = State()
    waiting_for_sum = State()
    waiting_for_comment = State()
    waiting_for_confirm = State()
    finish_all = State()


class DeletePayment(StatesGroup):
    waiting_for_history_choose = State()
    waiting_for_comment = State()
    waiting_for_search_restart = State()
    waiting_choose_number = State()
    waiting_for_confirm = State()


# States to use in user chat for feedback
class Feedback(StatesGroup):
    waiting_for_feedback_message = State()
