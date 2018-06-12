# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from datetime import datetime
import logging
import sys
import os
import uuid

from sqlalchemy import Column, ForeignKey, String, DateTime, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
logger = logging.getLogger(__name__)
engine = None
Session = None


def init(url):
    global engine
    engine = create_engine(url, connect_args={'check_same_thread': False})

    try:
        Base.metadata.create_all(engine)

        global Session
        Session = sessionmaker(bind=engine)

        logger.info('Database initialized.')
    except SQLAlchemyError as err:
        logger.error('Database could not be initialized. | %s' % err)
        sys.exit(1)


def get_session():
    return Session()


def get_engine():
    return engine


def make_uuid():
    return str(uuid.uuid4())


class Offset(Base):
    __tablename__ = 'offset'

    schema_name = Column(String, primary_key=True)
    offset_value = Column(String, nullable=False)

    @classmethod
    def create(cls, **kwargs):
        offset = Offset.get(**kwargs)
        if offset:
            return offset
        offset = cls(**kwargs)
        session = get_session()
        session.add(offset)
        session.commit()
        return offset

    @classmethod
    def get(cls, **kwargs):
        session = get_session()
        offset = session.query(cls).filter_by(**kwargs).first()
        return offset

    @classmethod
    def update(cls, name, offset):
        try:
            offset=Offset.get_offset(name)
            if offset:
                offset.offset_value = offset
                session = get_session()
                session.add(offset)
                session.commit()
                return offset
            else:
                raise ValueError('No row with matching name %s' % name)
        except Exception as err:
            logger.error('Could not save offset for topic %s | %s' % (name, err))
            return offset

    @classmethod
    def get_offset(cls, name):
        session = get_session()
        offset = session.query(cls).filter_by(
            schema_name=name
        ).first()
        return offset
