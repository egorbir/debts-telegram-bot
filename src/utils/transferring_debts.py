import random
from collections import defaultdict

from src.data.redis_interface import RedisInterface


def add_payment_total_redis(payment: dict, chat_id: str, redis: RedisInterface):
    """
    Get payment dict, write it to redis & change redis balances.
    Balances change: full read -> edit -> full write

    :param payment: payment dict from the bot
    :param chat_id: id of chat where the bot is running
    :param redis: Redis Interface
    :return: No return
    """

    balances = redis.read_chat_balances(chat_id=chat_id)
    balances[payment['payer']] += payment['sum']
    shared_payment = round(payment['sum'] / len(payment['debtors']))
    for debtor in payment['debtors']:
        balances[debtor] -= shared_payment
    redis.add_payment(chat_id=chat_id, payment=payment)
    redis.write_chat_balances(chat_id=chat_id, balances=balances)


def add_payment(payment: dict, chat_id: str, redis: RedisInterface):
    """
    Get payment dict, write it to redis & change redis balances.
    Balances changed one by one with special interface method

    :param payment: payment dict from the bot
    :param chat_id: id of chat where the bot is running
    :param redis: Redis Interface
    :return: No return
    """

    redis.increase_chat_user_balance(chat_id=chat_id, user=payment['payer'], increase_sum=payment['sum'])
    shared_payment = round(payment['sum'] / len(payment['debtors']), ndigits=2)
    for debtor in payment['debtors']:
        redis.decrease_chat_user_balance(chat_id=chat_id, user=debtor, decrease_sum=shared_payment)
    redis.add_payment(chat_id=chat_id, payment=payment)


def normalize_balances(balances: dict):
    """
    Normalize all balances in order to equal their sum to 0

    :param balances: dict of balances from Redis
    :return: normalized balances with 0 sum
    """

    b_sum = sum(balances.values())
    if b_sum != 0:
        random_user = random.choice(list(balances.keys()))
        balances[random_user] = float(format(balances[random_user] - b_sum, '.2f'))
    return balances


def balances_to_payments(chat_id: str, redis: RedisInterface) -> list[dict]:
    """
    Convert balances to money transfers in the end of the work.
    Creates list of transfers without any extra money travel

    :param chat_id: id of chat where the bot is running
    :param redis: Redis interface
    :return: list of money transfers to pay all the debts off
    """

    transfers = list()
    balances = redis.read_chat_balances(chat_id=chat_id)
    balances = normalize_balances(balances=balances)
    while any(balances.values()):
        negative = [{'name': name, 'balance': balance} for name, balance in balances.items() if balance < 0]
        positive = [{'name': name, 'balance': balance} for name, balance in balances.items() if balance > 0]
        min_positive = min(positive, key=lambda x: x['balance'])
        min_negative = min(negative, key=lambda x: x['balance'])
        sum_of_transfer = min(abs(min_negative['balance']), abs(min_positive['balance']))
        transfers.append({
            'from': min_negative['name'],
            'to': min_positive['name'],
            'payment': sum_of_transfer
        })
        balances[min_negative['name']] += sum_of_transfer
        balances[min_positive['name']] -= sum_of_transfer
    redis.write_chat_balances(chat_id=chat_id, balances=balances)  # TODO надо ли писать пустые балансы в редис??
    return transfers


def payments_to_balances(payments: list[dict]) -> dict[str, int]:
    """
    Convert history of payments to user balances.
    Can be useful in case of server restart and loss of actual balances data from Redis

    :param payments: list of payments history
    :return: recovered user balances
    """

    balances = defaultdict(lambda: 0)
    for payment in payments:
        balances[payment['payer']] -= payment['sum']
        for debtor in payment['debtors']:
            balances[debtor] += payment['sum']
    return dict(balances)
