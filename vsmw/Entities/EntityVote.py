from sqlalchemy import Column, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base

from vsmw.Entities.EntityBase import EntityBase

from vsmw.db import DBConnection

Base = declarative_base()

class EntityVote(EntityBase, Base):
    __tablename__ = 'vsmw_vote'

    session = Column(Integer, primary_key=True)
    user    = Column(String, primary_key=True)
    value   = Column(Integer, primary_key=True)

    json_serialize_items_list = ['session', 'user', 'value']

    def __init__(self, session, user, value):
        super().__init__()
        self.session    = session
        self.user       = str(user)
        self.value      = value

    def add(self):
        with DBConnection() as session:
            session.db.add(self)
            session.db.commit()
            return self.session

    @classmethod
    def stats(cls, id, type):
        with DBConnection() as session:
            if type == 'slider':
                res = list((session.db.query(
                    func.avg(EntityVote.value).label('average'),
                    func.count(EntityVote.value).label('count')
                ).filter_by(session=id).all())[0])
                if res[1] == 0:
                    res[0] = 0
            else:
                pos_size = \
                session.db.query(
                    func.count(EntityVote.value)
                ).filter_by(session=id).filter(EntityVote.value != 0).all()[0][0]

                neg_size = \
                session.db.query(
                    func.count(EntityVote.value)
                ).filter_by(session=id).filter(EntityVote.value == 0).all()[0][0]

                summ = pos_size + neg_size
                if summ > 0:
                    pos = int(float(pos_size) / summ * 100.0)

                    res = [pos, 100 - pos]
                else:
                    res = [0, 0]

            return [int(_) for _ in res]


