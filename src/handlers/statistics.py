from aiogram import types, Dispatcher

from src.data.redis_interface import RedisInterface

RDS = RedisInterface(host='localhost', port=6379, db=0, password=None)


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


def register_statistics_handlers(dp: Dispatcher):
    dp.register_message_handler(get_users_payments_stats, commands='stats', state='*')
