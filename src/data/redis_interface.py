import json

from redis.client import Redis


class RedisInterface:
    """
    Interface to implement redis interaction logic
    """

    def __init__(self, host, port, db, password):
        self.rds = Redis(host=host, port=port, db=db, password=password)

    def read_chat_balances(self, chat_id: str) -> dict:
        raw_balances = self.rds.hget(chat_id, 'balances')
        if raw_balances is not None:
            return json.loads(raw_balances.decode('utf-8'))
        else:
            return dict()

    def write_chat_balances(self, chat_id: str, balances: dict):
        self.rds.hset(chat_id, mapping={'balances': json.dumps(balances)})

    def read_chat_payments(self, chat_id: str) -> list[dict]:
        raw_payments = self.rds.hget(chat_id, 'payments')
        if raw_payments is not None:
            return json.loads(self.rds.hget(chat_id, 'payments').decode('utf-8'))
        else:
            return list()

    def write_chat_payments(self, chat_id: str, payments: list[dict]):
        self.rds.hset(chat_id, mapping={'payments': json.dumps(payments)})

    def add_payment(self, chat_id: str, payment: dict):
        payments = self.read_chat_payments(chat_id=chat_id)
        payments.append(payment)
        self.write_chat_payments(chat_id=chat_id, payments=payments)

    # TODO подумать надо ли оно, может проще читать целиком, менять и целиком записывать
    def increase_chat_user_balance(self, chat_id: str, user: str, increase_sum: float):
        balances = self.read_chat_balances(chat_id=chat_id)
        balances[user] += increase_sum
        self.write_chat_balances(chat_id=chat_id, balances=balances)

    def decrease_chat_user_balance(self, chat_id: str, user: str, decrease_sum: float):
        balances = self.read_chat_balances(chat_id=chat_id)
        balances[user] -= decrease_sum
        self.write_chat_balances(chat_id=chat_id, balances=balances)

    def initialize_chat_redis(self, chat_id: str):
        if not self.rds.exists(chat_id):
            self.write_chat_balances(chat_id=chat_id, balances=dict())
            self.write_chat_payments(chat_id=chat_id, payments=list())
