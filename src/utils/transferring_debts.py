import copy
import random
from collections import defaultdict


def add_payment(payment: dict, balances_to_add: dict, payments_to_add: list[dict]):
    balances_to_add[payment['payer']] += payment['sum']
    shared_payment = round(payment['sum'] / len(payment['debtors']))
    for debtor in payment['debtors']:
        balances_to_add[debtor] -= shared_payment
    payments_to_add.append(payment)


def normalize_balances(balances: dict):
    b_sum = sum(balances.values())
    if b_sum != 0:
        balances[random.choice(list(balances.keys()))] -= b_sum
    return balances


def balances_to_payments(balances: dict[str, int]) -> list[dict]:
    payments = list()
    balances = copy.deepcopy(balances)
    balances = normalize_balances(balances=balances)
    while any(balances.values()):
        negative = [{'name': name, 'balance': balance} for name, balance in balances.items() if balance < 0]
        positive = [{'name': name, 'balance': balance} for name, balance in balances.items() if balance > 0]
        min_positive = min(positive, key=lambda x: x['balance'])
        min_negative = min(negative, key=lambda x: x['balance'])
        sum_of_transfer = min(abs(min_negative['balance']), abs(min_positive['balance']))
        payments.append({
            'from': min_negative['name'],
            'to': min_positive['name'],
            'payment': sum_of_transfer
        })
        balances[min_negative['name']] += sum_of_transfer
        balances[min_positive['name']] -= sum_of_transfer
    return payments


def payments_to_balances(payments: list[dict]) -> dict[str, int]:
    payments = copy.deepcopy(payments)
    balances = defaultdict(lambda: 0)
    for payment in payments:
        balances[payment['from']] -= payment['payment']
        balances[payment['to']] += payment['payment']
    return dict(balances)
