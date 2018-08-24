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
    __tablename__ = 'vsmw_session'

    vid = Column(Integer, Sequence('vsmw_seq'), primary_key=True)
    title   = Column(String)
    type    = Column(String)
    image   = Column(String)
    created = Column(Date)
    updated = Column(Date)
    expires = Column(Date)

    json_serialize_items_list = ['vid', 'title', 'type', 'image', 'created', 'updated', 'expires']
    editable_items_list = ['title', 'type', 'image', 'expires']

    def __init__(self, title, type, image, expires):
        super().__init__()

        self.title = title
        self.type = type
        self.image = image

        ts = time.time()
        self.created = self.updated = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        self.expires = expires

    @classmethod
    def add_from_params(cls, data):
        try:
            if all([_ in data for _ in cls.editable_items_list]):
                title   = data['title']
                type    = data['type']
                picture = data['image']
                expires = data['expires']

                resolver = MediaResolverFactory.produce('image', picture)
                picture_url = resolver.Resolve()

                return EntitySession(title, type, picture_url, expires).add()
        except:
            return None

        return None

    @classmethod
    def update_from_params(cls, data):
        def proxy(data, field):
            if field == 'image':
                resolver = MediaResolverFactory.produce('image', data[field])
                return resolver.Resolve()

            return data[field]

        try:
            if 'id' in data:
                with DBConnection() as session:
                    vid = data['id']
                    entity = session.db.query(EntitySession).filter_by(vid=vid).all()

                    if len(entity):
                        for _ in entity:
                            for field in cls.editable_items_list:
                                setattr(_, field, proxy(data, field) if field in data else getattr(_, field, None))

                        session.db.commit()
                        return vid
        except:
            return None

        return None