from aiogram.dispatcher.filters.state import State, StatesGroup


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
