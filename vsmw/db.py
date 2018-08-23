from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker

class DBConnection:
    s_owner_token = None

    s_dbParams = {
        'host': '185.122.59.110',
        'port': 5433,
        'sid': 'each_dev',
        'user': 'each',
        'password': "Ellesmera2006",
        'pool_size': 2
    }

    @classmethod
    def configure(cls, **kwargs):
        cls.s_dbParams.update(kwargs)
        dsn = URL("postgresql", username=cls.s_dbParams['user'], password=cls.s_dbParams['password'],
                  host=cls.s_dbParams['host'], port=cls.s_dbParams['port'], database=cls.s_dbParams['sid'])

        cls.engine = create_engine(dsn, pool_size=cls.s_dbParams['pool_size'])       # create a configured "Session" class
        cls.Session = sessionmaker(bind=cls.engine)

    def __init__(self, logger=None):
        p = self.s_dbParams
        p.update({'logger': logger})
        self.open()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def __acquire_connection(self):
        # conn = self.engine.connect()
        session = self.Session()

        return session

    def __release_connection(self, session):
        session.close()
        # conn.close()

    def open(self):
        self.db = self.__acquire_connection()

    def close(self):
        self.__release_connection(self.db)
