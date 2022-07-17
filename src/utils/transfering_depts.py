import copy
import random
from collections import defaultdict

db_balances = {
    'Egor': 500,
    'Grisha': -1000,
    'Den': 150
}

db_payments = list()


def add_person(balances: dict[str, int], name: str) -> dict[str, int]:
    # TODO: подумать насчет ипользования db_balances напрямую (фактически - глоб. переменная, так-то не очень хорошо)
    # Если не использовать напрямую - придется каждый раз делать глубокую копию и возвращать новый объект
    # В очень больших компаниях придет пизда :)
    balances[name] = 0
    return balances


def add_payment(payment: dict, balances_to_add: dict):
    balances_to_add[payment['payer']] += payment['sum']
    shared_payment = round(payment['sum'] / len(payment['debtors']))
    for debtor in payment['debtors']:
        balances_to_add[debtor] -= shared_payment
    db_payments.append(payment)


def normalize_balances(balances: dict):
    # А вот тут уже как раз можно и без return, потому что функа должна юзаться только внутри другой функи
    # Но это справедливо только в том случае, если в balances_to_payments будет делаться глубокая копия
    # Иначе изменение объекта насквозь через несколько слоев ф-ий - это полный пиздец
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

