from aiogram import Dispatcher, types

from src.handlers.constants import RDS


async def get_users_payments_stats(msg: types.Message):
    payments = RDS.read_chat_payments(chat_id=msg.chat.id)
    stats = dict()
    for payment in payments:
        if payment['payer'] not in stats:
            stats[payment['payer']] = {
                'sum': payment['sum'],
                'count': 1
            }
        else:
            stats[payment['payer']['sum']] += payment['sum']
            stats[payment['payer']['count']] += 1
    result_message = 'Statistics of amounts: \n\n'
    for user, stat in stats.items():
        result_message += f'{user} made {stat["count"]} payments, spent - {stat["sum"]}\n\n'
    await msg.answer(text=result_message)


async def list_payments(msg: types.Message):
    payments = RDS.read_chat_payments(chat_id=msg.chat.id)  # TODO read from DB instead of redis
    if len(payments) == 0:
        await msg.answer('No payments yet')
    else:
        reply_msg_template = 'History of payments:\n'
        for payment in payments:
            reply_msg_template += f'\nPayment:\n\n{payment["payer"]} payed for {", ".join(payment["debtors"])}\n' \
                                  f'Sum: {payment["sum"]}\nDate: {payment["date"]}'
            if payment['comment'] != '':
                reply_msg_template += f'\nComment: {payment["comment"]}'
            reply_msg_template += '\n_________________________________\n'
        await msg.answer(reply_msg_template)


def register_statistics_handlers(dp: Dispatcher):
    dp.register_message_handler(get_users_payments_stats, commands='stats')
    dp.register_message_handler(list_payments, commands='history')
