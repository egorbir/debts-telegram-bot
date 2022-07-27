import json
from typing import Optional

from redis.client import Redis


class RedisInterface:
    """
    Interface to implement redis interaction logic
    """

    def __init__(self, host, port, db, password):
        self.rds = Redis(host=host, port=port, db=db, password=password)

    def read_chat_debts_group_name(self, chat_id: str) -> Optional[str]:
        """
        Get current debts group name from chat redis
        :param chat_id: telegram chat id where bot is working
        :return: found group name or None
        """

        return self.rds.hget(chat_id, 'group_name').decode('utf-8') if \
            self.rds.hget(chat_id, 'group_name') is not None else None

    def write_chat_debts_group_name(self, chat_id: str, name: str):
        """
        Put current debts group name to chat redis
        :param chat_id: telegram chat id where bot is working
        :param name: debts group name to write in redis
        """

        self.rds.hset(chat_id, mapping={'group_name': name})

    def read_chat_balances(self, chat_id: str) -> dict:
        """
        Get current chat balances from redis
        :param chat_id: telegram chat id where bot is working
        :return: dict of usernames balances
        """

        raw_balances = self.rds.hget(chat_id, 'balances')
        if raw_balances is not None:
            return json.loads(raw_balances.decode('utf-8'))
        else:
            return dict()

    def write_chat_balances(self, chat_id: str, balances: dict):
        """
        Put current chat balances to redis
        :param chat_id: telegram chat id where bot is working
        :param balances: dict of usernames balances to write to redis
        """

        self.rds.hset(chat_id, mapping={'balances': json.dumps(balances)})

    def read_chat_payments(self, chat_id: str) -> list[dict]:
        """
        Get chat payments history from redis
        :param chat_id: telegram chat id where bot is working
        :return: list of dicts with payments
        """

        raw_payments = self.rds.hget(chat_id, 'payments')
        if raw_payments is not None:
            return json.loads(self.rds.hget(chat_id, 'payments').decode('utf-8'))
        else:
            return list()

    def write_chat_payments(self, chat_id: str, payments: list[dict]):
        """
        Put payments to chat redis
        :param chat_id: telegram chat id where bot is working
        :param payments: list of payments to write to redis
        """

        self.rds.hset(chat_id, mapping={'payments': json.dumps(payments)})

    def add_payment(self, chat_id: str, payment: dict):
        payments = self.read_chat_payments(chat_id=chat_id)
        payments.append(payment)
        self.write_chat_payments(chat_id=chat_id, payments=payments)

    def increase_chat_user_balance(self, chat_id: str, user: str, increase_sum: float):
        """
        Add sum to user balance in chat redis
        :param chat_id: telegram chat id where bot is working
        :param user: username to increase balance
        :param increase_sum: money sum add to balance
        """

        balances = self.read_chat_balances(chat_id=chat_id)
        balances[user] = float(format(balances[user] + increase_sum, '.2f'))
        self.write_chat_balances(chat_id=chat_id, balances=balances)

    def decrease_chat_user_balance(self, chat_id: str, user: str, decrease_sum: float):
        """
        Subtract sum from user balance in chat redis
        :param chat_id: telegram chat id where bot is working
        :param user: username to decrease balance
        :param decrease_sum: money sum subtract from balance
        """

        balances = self.read_chat_balances(chat_id=chat_id)
        balances[user] = float(format(balances[user] - decrease_sum, '.2f'))
        self.write_chat_balances(chat_id=chat_id, balances=balances)

    def initialize_chat_redis(self, chat_id: str, group_name: str, balances: dict = None, payments: list = None):
        """
        Initialize chat redis with data
        :param chat_id: telegram chat id where bot is working
        :param group_name: name of debts group
        :param balances: dict of username balances
        :param payments: list of payments
        """

        init_balances = balances or dict()
        init_payments = payments or list()
        self.write_chat_debts_group_name(chat_id=chat_id, name=group_name)
        self.write_chat_balances(chat_id=chat_id, balances=init_balances)
        self.write_chat_payments(chat_id=chat_id, payments=init_payments)
