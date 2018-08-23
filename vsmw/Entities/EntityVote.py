from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

from vsmw.Entities.EntityBase import EntityBase

Base = declarative_base()

class EntityVote(EntityBase, Base):
    __tablename__ = 'vsmw_vote'

    session = Column(Integer, primary_key=True)
    user    = Column(Integer, primary_key=True)
    value   = Column(Integer, primary_key=True)

    json_serialize_items_list = ['session', 'user', 'value']

    def __init__(self, session, user, value):
        super().__init__()
        self.session    = session
        self.user       = user
        self.value      = value

