import json

from redis.client import Redis


class RedisInterface:
    """
    Interface to implement redis interaction logic.
    Redis is used primarily for storing users balances.
    Balances are the central element of calculation algorith, updated after each payment and different for every chat.
    Balances represent current state of the group of payments, can be restored using history of payments.
    """

    def __init__(self, host, port, password):
        self.rds = Redis(host=host, port=port, password=password)

    def _write_chat_debts_group_name(self, chat_id: str, name: str):
        """
        Put current debts group name to chat redis
        :param chat_id: telegram chat id where bot is working
        :param name: debts group name to write in redis
        """

        self.rds.hset(chat_id, mapping={"group_name": name})

    def _read_chat_balances(self, chat_id: str) -> dict:
        raw_balances = self.rds.hget(chat_id, "balances")
        if raw_balances is not None:
            return json.loads(raw_balances.decode("utf-8"))
        else:
            return dict()

    def _write_chat_balances(self, chat_id: str, balances: dict):
        """
        Put current chat balances to redis
        :param chat_id: telegram chat id where bot is working
        :param balances: dict of usernames balances to write to redis
        """

        self.rds.hset(chat_id, mapping={"balances": json.dumps(balances)})

    def _increase_chat_user_balance(self, chat_id: str, user: str, increase_sum: float):
        """
        Add amount to user balance in chat redis
        :param chat_id: telegram chat id where bot is working
        :param user: username to increase balance
        :param increase_sum: money amount add to balance
        """

        balances = self._read_chat_balances(chat_id=chat_id)
        balances[user] = float(format(balances[user] + increase_sum, ".2f"))
        self._write_chat_balances(chat_id=chat_id, balances=balances)

    def _decrease_chat_user_balance(self, chat_id: str, user: str, decrease_sum: float):
        """
        Subtract amount from user balance in chat redis
        :param chat_id: telegram chat id where bot is working
        :param user: username to decrease balance
        :param decrease_sum: money amount subtract from balance
        """

        balances = self._read_chat_balances(chat_id=chat_id)
        balances[user] = float(format(balances[user] - decrease_sum, ".2f"))
        self._write_chat_balances(chat_id=chat_id, balances=balances)

    def get_chat_debts_group_name(self, chat_id: str) -> str | None:
        """
        Get current debts group name from chat redis
        :param chat_id: telegram chat id where bot is working
        :return: found group name or None
        """

        return self.rds.hget(chat_id, "group_name").decode("utf-8") if \
            self.rds.hget(chat_id, "group_name") is not None else None

    def get_chat_balances(self, chat_id: str) -> dict:
        """
        Get current chat balances from redis
        :param chat_id: telegram chat id where bot is working
        :return: dict of usernames balances
        """

        return self._read_chat_balances(chat_id=chat_id)

    def add_chat_payment_update_balances(self, chat_id: str, payment: dict):
        """
        Get payment dict and change redis balances.
        Balances changed one by one

        :param payment: payment dict from the bot
        :param chat_id: id of chat where the bot is running
        """

        self._increase_chat_user_balance(chat_id=chat_id, user=payment["payer"], increase_sum=payment["amount"])
        shared_payment = round(payment["amount"] / len(payment["debtors"]), ndigits=2)
        for debtor in payment["debtors"]:
            self._decrease_chat_user_balance(chat_id=chat_id, user=debtor, decrease_sum=shared_payment)

    def delete_chat_payment_update_balances(self, chat_id: str, payment: dict):
        """
        Delete payment from chat redis by its ID
        :param chat_id: telegram chat id where bot is working
        :param payment: dict of payment to be deleted
        """

        self._decrease_chat_user_balance(chat_id=chat_id, user=payment["payer"], decrease_sum=payment["amount"])
        shared_payment = round(payment["amount"] / len(payment["debtors"]), ndigits=2)
        for debtor in payment["debtors"]:
            self._increase_chat_user_balance(chat_id=chat_id, user=debtor, increase_sum=shared_payment)

    def add_user_to_balances(self, chat_id: str, username: str) -> bool:
        """
        Add username to balances of chat with chat_id with 0 initial balance
        :param chat_id: telegram chat ID
        :param username: user telegram username
        :return: bool, True if user added successfully, False if user is already in chat balances
        """

        balances = self._read_chat_balances(chat_id=chat_id)
        if username not in balances:
            balances[username] = 0
            self._write_chat_balances(chat_id=chat_id, balances=balances)
            return True
        else:
            return False

    def remove_user_from_balances(self, chat_id: str, username: str) -> bool:
        """
        Remove username from balances of chat with chat_id (only if no all balances are 0)
        :param chat_id: telegram chat ID
        :param username: user telegram username
        :return: bool, True if user removed successfully, False if any balance is not 0
        """

        balances = self._read_chat_balances(chat_id=chat_id)
        if not any(balances.values()):
            balances.pop(username, None)
            self._write_chat_balances(chat_id=chat_id, balances=balances)
            return True
        else:
            return False

    def initialize_chat_redis(self, chat_id: str, group_name: str, balances: dict = None):
        """
        Initialize chat redis with interfaces
        :param chat_id: telegram chat id where bot is working
        :param group_name: name of debts group
        :param balances: dict of username balances
        """

        init_balances = balances or dict()
        self._write_chat_debts_group_name(chat_id=chat_id, name=group_name)
        self._write_chat_balances(chat_id=chat_id, balances=init_balances)
