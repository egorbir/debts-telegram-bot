from aiogram import Dispatcher, types

from src.handlers.constants import RDS, DB


async def get_users_payments_stats(msg: types.Message):
    """
    Print statistics of users payments amounts
    """

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
    result_message = 'Статистика по потраченным суммам: \n\n'
    for user, stat in stats.items():
        # result_message += f'{user} made {stat["count"]} payments, spent - {stat["sum"]}\n\n'
        result_message += f'{user} сделал {stat["count"]} платежей, потрачено - {stat["sum"]}\n\n'
    await msg.answer(text=result_message)


async def list_payments(msg: types.Message):
    """
    Print payments history
    """

    chat_id = str(msg.chat.id)
    group_name = RDS.read_chat_debts_group_name(chat_id=chat_id)
    payments = DB.get_chat_group_payments(chat_id=chat_id, group_name=group_name)['payments']
    if len(payments) == 0:
        message = 'No payments yet'
        message = 'Платежей еще не было'
        await msg.answer(message)
    else:
        # reply_msg_template = 'History of payments:\n'
        reply_msg_template = 'История платежей:\n'
        for payment in payments:
            # reply_msg_template += f'\nPayment:\n\n{payment["payer"]} payed for {", ".join(payment["debtors"])}\n' \
            #                       f'Sum: {payment["sum"]}\nDate: {payment["date"]}'
            reply_msg_template += f'\nПлатеж:\n\n{payment["payer"]} заплатил за {", ".join(payment["debtors"])}\n' \
                                  f'Сумма: {payment["sum"]}\nДата: {payment["date"]}'
            if payment['comment'] != '':
                # reply_msg_template += f'\nComment: {payment["comment"]}'
                reply_msg_template += f'\nКомментарий: {payment["comment"]}'
            reply_msg_template += '\n_________________________________\n'
        await msg.answer(reply_msg_template)


def register_statistics_handlers(dp: Dispatcher):
    dp.register_message_handler(get_users_payments_stats, commands='stats')
    dp.register_message_handler(list_payments, commands='history')
