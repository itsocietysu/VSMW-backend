from sqlalchemy import Column, Integer, Sequence
from sqlalchemy.ext.declarative import declarative_base

from vsmw.Entities.EntityBase import EntityBase

Base = declarative_base()

class EntityUser(EntityBase, Base):
    __tablename__ = 'vsmw_user'

    vid = Column(Integer, Sequence('vsmw_seq'), primary_key=True)
    fingerprint    = Column(Integer)

    json_serialize_items_list = ['vid', 'fingerprint']

    def __init__(self, fingerprint):
        super().__init__()
        self.fingerprint = fingerprint
