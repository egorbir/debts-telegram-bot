from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from src.handlers.constants import DB, RDS, Register
from src.handlers.utils import create_cancel_keyboard
from src.utils.transferring_debts import payments_to_balances


async def start(msg: types.Message):
    if RDS.read_chat_debts_group_name(chat_id=msg.chat.id) is not None:
        await msg.answer('Group is already in progress, you can only /newgroup to create a new one')
    else:
        hello_message = 'This is bot for counting group debts\nTo start counting enter short group name (ex. the ' \
                        'name of an event or the country/city of a trip etc.)\nBe careful, this name cannot be ' \
                        'edited, only create new'
        await msg.answer(text=hello_message)
        await Register.waiting_for_group_name.set()


async def new_group(msg: types.Message):
    msg_txt = 'Enter the name of new group. Be careful, all new payments will be saved to this new group.'
    await msg.answer(text=msg_txt, reply_markup=create_cancel_keyboard())
    await Register.waiting_for_group_name.set()


async def get_group_name(msg: types.Message, state: FSMContext):
    if msg.text.startswith('/') or '@RepetitionsBot' in msg.text:  # TODO replace bot username
        await msg.answer('No commands, finish process first')
        return
    chat_id = str(msg.chat.id)
    group_name = msg.text.strip().replace(' ', '_')
    if group_name not in DB.get_chat_groups(chat_id=chat_id):
        DB.add_chat_group(chat_id=chat_id, group_name=group_name)
        RDS.initialize_chat_redis(chat_id=msg.chat.id, group_name=group_name)
        user_registration_msg = 'Your group started! Now everyone who is in this group please tap the command /reg\n' \
                                'To exit group use /unreg (you can exit only if there are no payments yet)'
        await msg.answer(user_registration_msg)
        await state.finish()
    else:
        await msg.answer(text='Group with this name already exists. Type another name.')


async def register_user(msg: types.Message):
    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'
    redis_balances = RDS.read_chat_balances(chat_id=msg.chat.id)
    if username not in redis_balances:
        redis_balances[username] = 0
        message = f'Good, now you are in group - {username}'
    else:
        message = 'Already in group'
    await msg.answer(text=message)
    RDS.write_chat_balances(chat_id=msg.chat.id, balances=redis_balances)


async def unregister_user(msg: types.Message):
    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'
    balances = RDS.read_chat_balances(chat_id=msg.chat.id)
    if len(RDS.read_chat_payments(chat_id=msg.chat.id)) == 0:
        balances.pop(username, None)
        result_msg = f'User {username} successfully deleted from group'
        RDS.write_chat_balances(chat_id=msg.chat.id, balances=balances)
    else:
        result_msg = 'There are already payments in this group, ypu cannot leave'
    await msg.answer(result_msg)


async def restart(msg: types.Message):
    old_groups = DB.get_chat_groups(chat_id=str(msg.chat.id))
    message = f'Old groups - {", ".join([g.replace("_", " ") for g in old_groups])}. Type exact name of the ' \
              f'group to restart it'
    await msg.answer(text=message, reply_markup=create_cancel_keyboard())
    await Register.waiting_for_restart_group_name.set()


async def restart_group_name(msg: types.Message, state: FSMContext):
    if msg.text.startswith('/') or '@RepetitionsBot' in msg.text:  # TODO replace bot username
        await msg.answer('No commands, finish process first')
        return
    chat_id = str(msg.chat.id)
    group_name = msg.text.strip().replace(" ", "_")
    if group_name in DB.get_chat_groups(chat_id=chat_id):
        old_payments = DB.get_chat_group_payments(chat_id=chat_id, group_name=group_name)['payments']
        restart_balances = payments_to_balances(payments=old_payments)
        RDS.initialize_chat_redis(
            chat_id=chat_id,
            group_name=group_name,
            balances=restart_balances,
            payments=old_payments
        )
        message = f'Group {group_name} restarted. Has {len(old_payments)} payments'
        await state.finish()
    else:
        message = 'No such group retype EXACT name'
    await msg.answer(text=message)


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands='start')
    dp.register_message_handler(new_group, commands='newgroup')
    dp.register_message_handler(restart, commands='restart')
    dp.register_message_handler(restart_group_name, state=Register.waiting_for_restart_group_name)
    dp.register_message_handler(get_group_name, state=Register.waiting_for_group_name)
    dp.register_message_handler(register_user, commands='reg')
    dp.register_message_handler(unregister_user, commands='unreg')
