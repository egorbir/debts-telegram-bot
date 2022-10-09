import contextlib
from typing import Optional

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data import model


class DBInterface:
    """
    Interface to implement database connection logic
    Postgres database is used to store payments history
    """

    def __init__(self, user, password, database_name, host, port):
        self.engine = create_engine(
            f"postgresql://{user}:{password}@{host}:{port}/{database_name}",
            pool_size=30,
            max_overflow=0,
        )
        self.global_session = sessionmaker()
        self.global_session.configure(bind=self.engine)

        if not sqlalchemy.inspect(self.engine).has_table(model.PaymentsGroup.__tablename__):
            model.Base.metadata.create_all(self.engine)

    @contextlib.contextmanager
    def open_session(self, global_session):
        session = global_session()
        yield session
        session.close()

    def get_chat_groups(self, chat_id: str) -> list[str]:
        """
        Get all payment groups for chat id
        :param chat_id: telegram chat id where bot is working
        :return: list of payments groups
        """

        with self.open_session(self.global_session) as session:
            chat_payments_group = session.query(model.PaymentsGroup).filter(
                model.PaymentsGroup.chat_id == chat_id
            ).all()
        return list({cq.group_name for cq in chat_payments_group}) if chat_payments_group is not None else []

    def add_chat_group(self, chat_id: str, group_name: str):
        """
        Add new payments group to chat
        :param chat_id: telegram chat id where bot is working
        :param group_name: name of the group to add
        """

        if group_name not in self.get_chat_groups(chat_id=chat_id):
            with self.open_session(self.global_session) as session:
                new_chat_payments_group = model.PaymentsGroup(chat_id=chat_id, group_name=group_name, payments=[])
                session.add(new_chat_payments_group)
                session.commit()

    def add_chat_group_payment(self, chat_id: str, group_name: str, payment: dict):
        """
        Add new payment to chat group database
        :param chat_id: telegram chat id where bot is working
        :param group_name: name of payments group where add payment
        :param payment: dict of payment to be added
        """

        with self.open_session(self.global_session) as session:
            chat_payments_group = session.query(model.PaymentsGroup).filter(
                model.PaymentsGroup.chat_id == chat_id,
                model.PaymentsGroup.group_name == group_name
            ).first()
            chat_payments_group.payments.append(payment)
            session.commit()

    def delete_chat_group_payment(self, chat_id: str, group_name: str, payment_id: str):
        """
        Delete payment from payments group with name group_name of chat with chat_id by payment ID
        :param chat_id: telegram chat id where bot is working
        :param group_name: name of payments group where add payment
        :param payment_id: ID of payment ro delete
        """

        with self.open_session(self.global_session) as session:
            chat_payments_group = session.query(model.PaymentsGroup).filter(
                model.PaymentsGroup.chat_id == chat_id,
                model.PaymentsGroup.group_name == group_name
            ).first()
            for i, p in enumerate(chat_payments_group.payments):
                if p["id"] == payment_id:
                    del chat_payments_group.payments[i]
                    break
            session.commit()

    def get_all_chat_group_payments(self, chat_id: str, group_name: str) -> Optional[dict]:
        """
        Get payments for chat id and group name
        :param chat_id: telegram chat id where bot is working
        :param group_name: name of payments group (ex. mountains-ski-trip)
        :return: dict with payments of None if not found
        """

        with self.open_session(self.global_session) as session:
            chat_payments_group = session.query(model.PaymentsGroup).filter(
                model.PaymentsGroup.chat_id == chat_id,
                model.PaymentsGroup.group_name == group_name
            ).first()
        return chat_payments_group.serialize() if chat_payments_group is not None else None

    def get_chat_group_payment_by_id(self, chat_id: str, group_name: str, payment_id: str):
        """
        Get payment from payments group with name group_name of chat chat_id by payment ID
        :param chat_id: telegram chat id where bot is working
        :param group_name: name of payments group where add payment
        :param payment_id: ID of payment ro delete
        """

        with self.open_session(self.global_session) as session:
            chat_payments_group = session.query(model.PaymentsGroup).filter(
                model.PaymentsGroup.chat_id == chat_id,
                model.PaymentsGroup.group_name == group_name
            ).first()
        return next(payment for payment in chat_payments_group.payments if payment["id"] == payment_id)

