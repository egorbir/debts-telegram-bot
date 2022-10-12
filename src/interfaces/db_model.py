from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_json import mutable_json_type

Base = declarative_base()


class PaymentsGroup(Base):
    """
    Chat payments table
    """

    __tablename__ = "t_chat_payments"

    chat_id = Column(String(100), primary_key=True)
    group_name = Column(String(100), primary_key=True)
    payments = Column(mutable_json_type(dbtype=JSONB, nested=True))

    def __repr__(self):
        return f"Chat: {self.chat_id}, Group: {self.group_name}"

    def serialize(self):
        return {
            "chat_id": self.chat_id,
            "group_name": self.group_name,
            "payments": self.payments
        }
