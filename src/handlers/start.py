from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from src.data.credentials import BOT_NAME
from src.handlers.constants import DB, RDS, Register
from src.handlers.utils import create_cancel_keyboard, timeout
from src.utils.transferring_debts import payments_to_balances


@timeout(state_to_cancel='Register:waiting_for_group_name')
async def start(msg: types.Message, state: FSMContext):
    """
    Start command. Works only if there is no current debts group in progress
    """

    if msg.chat.type == types.ChatType.GROUP:
        if RDS.read_chat_debts_group_name(chat_id=msg.chat.id) is not None:
            hello_message = 'Group is already in progress, you can only /newgroup to create a new one'
            hello_message = 'Расчеты уже в процессе, можно только создать новую -  /newgroup'
            await msg.answer(hello_message)
        else:
            hello_message = 'This is bot for counting group debts\nTo start counting enter short group name (ex. the ' \
                            'name of an event or the country/city of a trip etc.)\nBe careful, this name cannot be ' \
                            'edited, only create new'
            hello_message = 'Этот бот помогает считать групповые долги\nЧтобы начать введите короткое имя новой группы ' \
                            'долгов (например, по названию поездки или мероприятия)\nБудьте внимательны, это название' \
                            'нельзя редактировать, только создать новую группу'
            await msg.answer(text=hello_message)
            await Register.waiting_for_group_name.set()
    elif msg.chat.type == types.ChatType.PRIVATE:
        await msg.answer('Привет! Этот бот предназначен для использования в группе с несколькими людьми.\n'
                         'Вызови справку командой /help или оставь свой отзыв командой /feedback')


@timeout(state_to_cancel='Register:waiting_for_restart_group_name')
async def restart(msg: types.Message, state: FSMContext):
    """
    Restart old debts group by its name. Gets all saved in database groups, print and waits for name input
    """

    old_groups = DB.get_chat_groups(chat_id=str(msg.chat.id))
    message = f'Old groups - {", ".join([g.replace("_", " ") for g in old_groups])}. Type exact name of the ' \
              f'group to restart it'
    message = f'Старые группы - [{", ".join([g.replace("_", " ") for g in old_groups])}]. Введите точное название ' \
              f'группы, что перезапустить ее'
    await msg.answer(text=message, reply_markup=create_cancel_keyboard())
    await Register.waiting_for_restart_group_name.set()


async def restart_group_name(msg: types.Message, state: FSMContext):
    """
    Get group name to restart it. Loads payments history and restores balances from payments. Ignores all commands
    """

    if msg.text.startswith('/') or BOT_NAME in msg.text:
        err_msg = 'No commands, finish process first'
        err_msg = 'Не вводите команды, пока процесс не завершен'
        await msg.answer(err_msg)
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
        message = f'Группа {group_name} перезапущена. В ней {len(old_payments)} платежей'
        await state.finish()
    else:
        message = 'No such group retype EXACT name'
        message = 'Группа не найдена, введите ТОЧНОЕ название'
    await msg.answer(text=message)


@timeout(state_to_cancel='Register:waiting_for_group_name')
async def new_group(msg: types.Message, state: FSMContext):
    """
    Create and start new debts group. Waits for new group name input
    """

    msg_txt = 'Enter the name of new group. Be careful, all new payments will be saved to this new group.'
    msg_txt = 'Введите имя новой группы. Будьте внимательны, все следующие платежи будут сохранены в эту новую группу.'
    await msg.answer(text=msg_txt, reply_markup=create_cancel_keyboard())
    await Register.waiting_for_group_name.set()


async def get_group_name(msg: types.Message, state: FSMContext):
    """
    Get new group name. Initialize DB and Redis. AFTER users need tot /reg. Ignores all commands in process
    """

    if msg.text.startswith('/') or BOT_NAME in msg.text:
        err_msg = 'No commands, finish process first'
        err_msg = 'Не вводите команды, пока процесс не завершен'
        await msg.answer(err_msg)
        return
    chat_id = str(msg.chat.id)
    group_name = msg.text.strip().replace(' ', '_')
    if group_name not in DB.get_chat_groups(chat_id=chat_id):
        DB.add_chat_group(chat_id=chat_id, group_name=group_name)
        RDS.initialize_chat_redis(chat_id=msg.chat.id, group_name=group_name)
        user_registration_msg = 'Your group started! Now everyone who is in this group please tap the command /reg\n' \
                                'To exit group use /unreg (you can exit only if there are no payments yet)'
        user_registration_msg = 'Новая группа начата! Все, кто участвует в расчетах, используйте команду /reg\n' \
                                'Выйти из группы - /unreg (только пока в группе нет платежей)'
        await msg.answer(user_registration_msg)
        await state.finish()
    else:
        message = 'Group with this name already exists. Type another name'
        message = 'Группа с таким именем уже существует. Введите другое'
        await msg.answer(text='.')


async def register_user(msg: types.Message):
    """
    Register user in current debts group. Add username to balances and set balance to 0
    """

    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'
    redis_balances = RDS.read_chat_balances(chat_id=msg.chat.id)
    if username not in redis_balances:
        redis_balances[username] = 0
        message = f'Good, now you are in group - {username}'
        message = f'Отлично, теперь ты у группе - {username}'
    else:
        message = 'Already in group'
        message = 'Ты уже в группе'
    await msg.answer(text=message)
    RDS.write_chat_balances(chat_id=msg.chat.id, balances=redis_balances)


async def unregister_user(msg: types.Message):
    """
    Unregister user. Delete username from balances. Only if there is no payments history
    """

    username = f'@{msg.from_user.username}'
    name = f'{msg.from_user.first_name} {msg.from_user.last_name}'
    balances = RDS.read_chat_balances(chat_id=msg.chat.id)
    if len(RDS.read_chat_payments(chat_id=msg.chat.id)) == 0:
        balances.pop(username, None)
        result_msg = f'User {username} successfully deleted from group'
        result_msg = f'Пользователь {username} удален из группы'
        RDS.write_chat_balances(chat_id=msg.chat.id, balances=balances)
    else:
        result_msg = 'There are already payments in this group, ypu cannot leave'
        result_msg = 'В группе уже есть платежи, из нее нельзя выйти'
    await msg.answer(result_msg)


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands='start')

    dp.register_message_handler(new_group, commands='newgroup', chat_type=types.ChatType.GROUP)
    dp.register_message_handler(restart, commands='restart', chat_type=types.ChatType.GROUP)

    dp.register_message_handler(
        restart_group_name, state=Register.waiting_for_restart_group_name, chat_type=types.ChatType.GROUP
    )
    dp.register_message_handler(get_group_name, state=Register.waiting_for_group_name, chat_type=types.ChatType.GROUP)

    dp.register_message_handler(register_user, commands='reg', chat_type=types.ChatType.GROUP)
    dp.register_message_handler(unregister_user, commands='unreg', chat_type=types.ChatType.GROUP)
