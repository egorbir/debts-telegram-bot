import contextlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DBInterface:
    """
    Interface to implement database connection logic
    """

    def __init__(self, host, port, user, password, database):
        self.engine = create_engine(
            f'postgresql://{user}:{password}@{host}:{port}/{database}',
            pool_size=30,
            max_overflow=0
        )
        self.global_session = sessionmaker(bind=self.engine)

    @contextlib.contextmanager
    def open_session(self, global_session):
        session = global_session()
        yield
        session.close()


class Core:
    def __init__(self, db: DBInterface):
        self.db = db
