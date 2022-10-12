import random
from collections import defaultdict


def normalize_balances(balances: dict):
    """
    Normalize all balances in order to equal their sum to 0

    :param balances: dict of balances from Redis
    :return: normalized balances with 0 sum
    """

    b_sum = sum(balances.values())
    if b_sum != 0:
        random_user = random.choice(list(balances.keys()))
        balances[random_user] = float(format(balances[random_user] - b_sum, ".2f"))
    return balances


def balances_to_transfers(balances: dict) -> list[dict]:
    """
    Convert balances to money transfers in the end of the work.
    Creates list of transfers without any extra money travel

    :param balances: dict of users balances
    :return: list of money transfers to pay all the debts off
    """

    transfers = list()
    balances = normalize_balances(balances=balances)
    while any(balances.values()):
        negative = [{"name": name, "balance": balance} for name, balance in balances.items() if balance < 0]
        positive = [{"name": name, "balance": balance} for name, balance in balances.items() if balance > 0]
        min_positive = min(positive, key=lambda x: x["balance"])
        min_negative = min(negative, key=lambda x: x["balance"])
        sum_of_transfer = min(abs(min_negative["balance"]), abs(min_positive["balance"]))
        transfers.append({
            "from": min_negative["name"],
            "to": min_positive["name"],
            "payment": sum_of_transfer
        })
        balances[min_negative["name"]] = float(format(balances[min_negative["name"]] + sum_of_transfer, ".2f"))
        balances[min_positive["name"]] = float(format(balances[min_positive["name"]] - sum_of_transfer, ".2f"))
    return transfers


def payments_to_balances(payments: list[dict]) -> dict[str, float]:
    """
    Convert history of payments to user balances.
    Can be useful in case of server restart and loss of actual balances interfaces from Redis

    :param payments: list of payments history
    :return: recovered user balances
    """

    balances = defaultdict(lambda: 0.0)
    for payment in payments:
        balances[payment["payer"]] = float(format(balances[payment["payer"]] + payment["sum"], ".2f"))
        shared_payment = round(payment["sum"] / len(payment["debtors"]))
        for debtor in payment["debtors"]:
            balances[debtor] = float(format(balances[debtor] - shared_payment, ".2f"))
    return dict(balances)
