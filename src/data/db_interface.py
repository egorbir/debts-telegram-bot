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

    def get_all_payments(self) -> list[dict]:
        """
        Get all payments that are stored in database
        :return: list of dicts, dict -> chat, group, payments
        """

        out = list()
        with self.open_session(self.global_session) as session:
            payments = session.query(Payment).all()
        if payments is not None:
            for payment in payments:
                out.append(payment.serialize())
        return out

    def get_chat_payments(self, chat_id: str) -> list[dict]:
        """
        Get all groups with payments for chat_id
        :param chat_id: str, telegram group id where bot is working
        :return: list of dicts, groups payments
        """

        out = list()
        with self.open_session(self.global_session) as session:
            chat_payments_query = session.query(Payment).filter(Payment.chat_id == chat_id).all()
        if chat_payments_query is not None:
            for payments in chat_payments_query:
                out.append(payments.serialize())
        return out

    def get_chat_groups(self, chat_id: str) -> list[str]:
        """
        Get all payment groups for chat id
        :param chat_id: str, telegram chat id where bot is working
        :return: list of payments groups
        """

        with self.open_session(self.global_session) as session:
            chat_payments = session.query(Payment).filter(Payment.chat_id == chat_id).all()
        return list({cq.group_name for cq in chat_payments}) if chat_payments is not None else []

    def get_chat_group_payments(self, chat_id: str, group_name: str) -> Optional[dict]:
        """
        Get payments for chat id and group name
        :param chat_id: str, telegram chat id where bot is working
        :param group_name: str, name of payments group (ex. mountains-ski-trip)
        :return: dict with payments of None if not found
        """

        with self.open_session(self.global_session) as session:
            chat_group_payments = session.query(Payment).filter(
                Payment.chat_id == chat_id,
                Payment.group_name == group_name
            ).first()
        return chat_group_payments.serialize() if chat_group_payments is not None else None

    def add_chat_group(self, chat_id: str, group_name: str):
        """
        Add new payments group to chat
        :param chat_id: str, telegram chat id where bot is working
        :param group_name: str, name of the group to add
        """

        if group_name not in self.get_chat_groups(chat_id=chat_id):
            with self.open_session(self.global_session) as session:
                new_chat_payments_object = Payment(chat_id=chat_id, group_name=group_name, payments=[])
                session.add(new_chat_payments_object)
                session.commit()

    def add_chat_group_payment(self, chat_id: str, group_name: str, payment: dict):
        """
        Add new payment to chat group database
        :param chat_id: str, telegram chat id where bot is working
        :param group_name: str, name of payments group where add payment
        :param payment: dict of payment to be added
        """

        with self.open_session(self.global_session) as session:
            chat_group_payment = session.query(Payment).filter(
                Payment.chat_id == chat_id,
                Payment.group_name == group_name
            ).first()
            chat_group_payment.payments.append(payment)
            session.commit()
