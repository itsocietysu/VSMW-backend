import base64
import datetime
import time

from sqlalchemy import Column, String, Integer, Date, Sequence
from sqlalchemy.ext.declarative import declarative_base

from vsmw.Entities.EntityBase import EntityBase

from vsmw.MediaResolver.MediaResolverFactory import MediaResolverFactory

from vsmw.db import DBConnection

Base = declarative_base()

class EntitySession(EntityBase, Base):
    __tablename__ = 'each_session'

    vid = Column(Integer, Sequence('vsmw_seq'), primary_key=True)
    title   = Column(String)
    type    = Column(String)
    picture = Column(String)
    created = Column(Date)
    updated = Column(Date)
    expires = Column(Date)

    json_serialize_items_list = ['eid', 'title', 'type', 'picture', 'created', 'updated', 'expires']
    editable_items_list = ['title', 'type', 'picture', 'expires']

    def __init__(self, title, type, picture, expires):
        super().__init__()

        self.title = title
        self.type = type
        self.picture = picture

        ts = time.time()
        self.created = self.updated = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        self.expires = expires

    @classmethod
    def add_from_json(cls, data):
        try:
            if 'title' in data and 'type' in data and 'picture' in data and 'expires' in data:
                title   = data['title']
                type    = data['type']
                picture = data['picture']
                expires = data['expires']

                resolver = MediaResolverFactory.produce('image', base64.b64decode(picture))
                picture_url = resolver.Resolve()

                return EntitySession(title, type, picture_url, expires).add()
        except:
            return None

        return None

    @classmethod
    def update_from_json(cls, data):
        try:
            if 'id' in data:
                with DBConnection() as session:
                    vid = data['id']
                    entity = session.db.query(EntitySession).filter_by(vid=vid).all()

                    if len(entity):
                        for _ in entity:
                            for field in cls.editable_items_list:
                                setattr(_, field, data[field] if field in data else getattr(_, field, None))

                        session.db.commit()
                        return vid
        except:
            return None

        return None