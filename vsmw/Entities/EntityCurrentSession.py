from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

from vsmw.Entities.EntityBase import EntityBase
from vsmw.db import DBConnection


Base = declarative_base()


class EntityCurrentSession(EntityBase, Base):
    __tablename__ = 'vsmw_curr_session'
    editable_items_list = ['curr_id']

    curr_id = Column(Integer, primary_key=True)

    def __init__(self, id):
        super().__init__()
        self.curr_id = id

    @classmethod
    def add_from_params(cls, data):
        try:
            if all([_ in data for _ in cls.editable_items_list]):
                curr_id = data['curr_id']
                return EntityCurrentSession(curr_id).add()
        except:
            return None

        return None

    @classmethod
    def update_from_params(cls, data):
        try:
            if 'curr_id' in data:
                with DBConnection() as session:
                    curr_id = data['curr_id']
                    entity = session.db.query(EntityCurrentSession).all()
                    if len(entity):
                        for _ in entity:
                            for field in cls.editable_items_list:
                                k = getattr(_, field, None)
                                setattr(_, field, data['curr_id'])

                        session.db.commit()
                        return curr_id
        except:
            return None

        return None