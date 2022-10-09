from aiogram import Dispatcher, types

from src.handlers.constants import RDS, DB


async def get_users_payments_stats(msg: types.Message):
    """
    Print statistics of users payments amounts
    """

    group_name = RDS.get_chat_debts_group_name(chat_id=msg.chat.id)
    payments = DB.get_all_chat_group_payments(chat_id=msg.chat.id, group_name=group_name)["payments"]
    stats = dict()
    for payment in payments:
        if payment["payer"] not in stats:
            stats[payment["payer"]] = {
                "sum": payment["sum"],
                "count": 1
            }
        else:
            stats[payment["payer"]["sum"]] += payment["sum"]
            stats[payment["payer"]["count"]] += 1
    result_message = "Statistics of amounts: \n\n"
    for user, stat in stats.items():
        result_message += f"{user} made {stat['count']} payments, spent - {stat['sum']}\n\n"
    await msg.answer(text=result_message)


async def list_payments(msg: types.Message):
    """
    Print payments history
    """

    group_name = RDS.get_chat_debts_group_name(chat_id=msg.chat.id)
    payments = DB.get_all_chat_group_payments(chat_id=msg.chat.id, group_name=group_name)["payments"]
    if len(payments) == 0:
        message = "No payments yet"
        await msg.answer(message)
    else:
        reply_msg_template = "History of payments:\n"
        for payment in payments:
            reply_msg_template += f"\nPayment:\n\n{payment['payer']} payed for {', '.join(payment['debtors'])}\n" \
                                  f"Amount: {payment['sum']}\nDate: {payment['date']}" \
                                  f"\nComment: {payment['comment']}" \
                                  f"\n_________________________________\n"
        await msg.answer(reply_msg_template)


def register_statistics_handlers(dp: Dispatcher):
    dp.register_message_handler(get_users_payments_stats, commands="stats", chat_type=types.ChatType.GROUP)
    dp.register_message_handler(list_payments, commands="history", chat_type=types.ChatType.GROUP)
