from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from src.data.credentials import BOT_NAME
from src.handlers.constants import DB, RDS, Register
from src.handlers.utils import create_cancel_keyboard, timeout
from src.utils.balances_processing import payments_to_balances


@timeout(state_to_cancel="Register:waiting_for_group_name")
async def start(msg: types.Message, state: FSMContext):
    """
    Start command. Works only if there is no current debts group in progress
    """

    if msg.chat.type == types.ChatType.GROUP:
        if RDS.get_chat_debts_group_name(chat_id=msg.chat.id) is not None:
            hello_message = "Group is already in progress, you can only /newgroup to create a new one"
            await msg.answer(hello_message)
        else:
            hello_message = "This is bot for counting group debts\nTo start counting enter short group name (ex. the " \
                            "name of an event or the country/city of a trip etc.)\nBe careful, this name cannot be " \
                            "edited, only create new"
            await msg.answer(text=hello_message)
            await Register.waiting_for_group_name.set()
    elif msg.chat.type == types.ChatType.PRIVATE:
        await msg.answer("Hello! This bot is designed to be used in a group with several people.\n"
                         "Call help with the command /help or leave your feedback with the command /feedback")


@timeout(state_to_cancel="Register:waiting_for_restart_group_name")
async def restart(msg: types.Message, state: FSMContext):
    """
    Restart old debts group by its name. Gets all saved in database groups, print and waits for name input
    """

    old_groups = DB.get_chat_groups(chat_id=str(msg.chat.id))
    message = f"Old groups - {', '.join([g.replace('_', ' ') for g in old_groups])}. Type exact name of the " \
              f"group to restart it"
    await msg.answer(text=message, reply_markup=create_cancel_keyboard())
    await Register.waiting_for_restart_group_name.set()


async def restart_group_name(msg: types.Message, state: FSMContext):
    """
    Get group name to restart it. Loads payments history and restores balances from payments. Ignores all commands
    """

    if msg.text.startswith("/") or BOT_NAME in msg.text:
        err_msg = "No commands, finish process first"
        await msg.answer(err_msg)
        return
    chat_id = str(msg.chat.id)
    group_name = msg.text.strip().replace(" ", "_")
    if group_name in DB.get_chat_groups(chat_id=chat_id):
        old_payments = DB.get_all_chat_group_payments(chat_id=chat_id, group_name=group_name)["payments"]
        restart_balances = payments_to_balances(payments=old_payments)
        RDS.initialize_chat_redis(
            chat_id=chat_id,
            group_name=group_name,
            balances=restart_balances
        )
        message = f"Group {group_name} restarted. Has {len(old_payments)} payments"
        await state.finish()
    else:
        message = "No such group retype EXACT name"
    await msg.answer(text=message)


@timeout(state_to_cancel="Register:waiting_for_group_name")
async def new_group(msg: types.Message, state: FSMContext):
    """
    Create and start new debts group. Waits for new group name input
    """

    msg_txt = "Enter the name of new group. Be careful, all new payments will be saved to this new group."
    await msg.answer(text=msg_txt, reply_markup=create_cancel_keyboard())
    await Register.waiting_for_group_name.set()


async def get_group_name(msg: types.Message, state: FSMContext):
    """
    Get new group name. Initialize DB and Redis. AFTER users need tot /reg. Ignores all commands in process
    """

    if msg.text.startswith("/") or BOT_NAME in msg.text:
        err_msg = "No commands, finish process first"
        await msg.answer(err_msg)
        return
    chat_id = str(msg.chat.id)
    group_name = msg.text.strip().replace(" ", "_")
    if group_name not in DB.get_chat_groups(chat_id=chat_id):
        DB.add_chat_group(chat_id=chat_id, group_name=group_name)
        RDS.initialize_chat_redis(chat_id=msg.chat.id, group_name=group_name)
        user_registration_msg = "Your group started! Now everyone who is in this group please tap the command /reg\n" \
                                "To exit group use /unreg (you can exit only if there are no payments yet)"
        await msg.answer(user_registration_msg)
        await state.finish()
    else:
        message = "Group with this name already exists. Type another name"
        await msg.answer(text=message)


async def register_user(msg: types.Message):
    """
    Register user in current debts group. Add username to balances and set balance to 0
    """

    username = f"@{msg.from_user.username}"
    if RDS.add_user_to_balances(chat_id=msg.chat.id, username=username):
        message = f"Good, now you are in group - {username}"
    else:
        message = "Already in group"
    await msg.answer(text=message)


async def unregister_user(msg: types.Message):
    """
    Unregister user. Delete username from balances. Only if there is no payments history
    """

    username = f"@{msg.from_user.username}"
    if RDS.remove_user_from_balances(chat_id=msg.chat.id, username=username):
        result_msg = f"User {username} successfully deleted from group"
    else:
        result_msg = "There are already payments in this group, ypu cannot leave"
    await msg.answer(result_msg)


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands="start")

    dp.register_message_handler(new_group, commands="newgroup", chat_type=types.ChatType.GROUP)
    dp.register_message_handler(restart, commands="restart", chat_type=types.ChatType.GROUP)

    dp.register_message_handler(
        restart_group_name, state=Register.waiting_for_restart_group_name, chat_type=types.ChatType.GROUP
    )
    dp.register_message_handler(get_group_name, state=Register.waiting_for_group_name, chat_type=types.ChatType.GROUP)

    dp.register_message_handler(register_user, commands="reg", chat_type=types.ChatType.GROUP)
    dp.register_message_handler(unregister_user, commands="unreg", chat_type=types.ChatType.GROUP)
