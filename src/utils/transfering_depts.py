db_balances = {
    'Egor': 500,
    'Grisha': -1000,
    'Den': 150
}


def add_payment(payment: dict):
    db_balances[payment['payer']] += payment['sum']
    for debtor in payment['debtors']:
        db_balances[debtor] -= payment['sum']


def transform_debts_graph(loans: list[dict]):
    pass
