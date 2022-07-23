import contextlib
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.model import Payment


class DBInterface:
    """
    Interface to implement database connection logic
    """

    def __init__(self, user, password, database_name, host, port):
        self.engine = create_engine(
            f"postgresql://{user}:{password}@{host}:{port}/{database_name}",
            pool_size=30,
            max_overflow=0,
        )
        self.global_session = sessionmaker()
        self.global_session.configure(bind=self.engine)

    @contextlib.contextmanager
    def open_session(self, global_session):
        session = global_session()
        yield session
        session.close()

    def get_all_payments(self):
        out = list()
        with self.open_session(self.global_session) as session:
            payments = session.query(Payment).all()
        for payment in payments:
            out.append(payment.serialize())
        return out

    def get_chat_payments(self, chat_id: str) -> list[dict]:
        out = list()
        with self.open_session(self.global_session) as session:
            chat_payments_query = session.query(Payment).filter(Payment.chat_id == chat_id).all()
        for payments in chat_payments_query:
            out.append(payments.serialize())
        return out

    def get_chat_groups(self, chat_id: str) -> list[str]:
        with self.open_session(self.global_session) as session:
            chat_payments = session.query(Payment).filter(chat_id == chat_id).all()
        return list({cq.group_name for cq in chat_payments})

    def get_chat_group_payments(self, chat_id: str, group_name: str) -> Optional[dict]:
        if group_name not in self.get_chat_groups(chat_id=chat_id):
            return None
        with self.open_session(self.global_session) as session:
            chat_group_payments = session.query(Payment).filter(
                Payment.chat_id == chat_id,
                Payment.group_name == group_name
            ).first()
        return chat_group_payments.serialize()

    def add_chat_group(self, chat_id: str, group_name: str):
        if group_name not in self.get_chat_groups(chat_id=chat_id):
            with self.open_session(self.global_session) as session:
                new_chat_payments_object = Payment(chat_id=chat_id, group_name=group_name, payments=[])
                session.add(new_chat_payments_object)
                session.commit()

    def add_chat_group_payment(self, chat_id, group_name, payment):
        with self.open_session(self.global_session) as session:
            chat_group_payment = session.query(Payment).filter(
                Payment.chat_id == chat_id,
                Payment.group_name == group_name
            ).first()
            chat_group_payment.payments.append(payment)
            session.commit()
