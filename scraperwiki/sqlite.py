from collections import Iterable, Mapping

import atexit
import datetime
import os
import re
import time
import sys
import warnings

DATABASE_NAME = os.environ.get("SCRAPERWIKI_DATABASE_NAME", "scraperwiki.sqlite")
DATABASE_TIMEOUT = float(os.environ.get("SCRAPERWIKI_DATABASE_TIMEOUT", 300))

class _State(object):
    """
    This class maintains global state relating to the database such as
    table_name, connection. It does not form part of the public interface.
    """
    db_path = 'sqlite:///{}'.format(DATABASE_NAME)
    _connection = None
    _transaction = None
    table_name = 'swdada'
    vars_table_name = 'swvariables'
    
    @classmethod
    def connection(cls):
        if cls._connection is None:
            engine = sqlalchemy.create_engine(db_path, echo=True, 
                    connect_args={'timeout': DATABASE_TIMEOUT})
            cls._connection = engine.connect()
            cls.new_transaction()

    @classmethod
    def new_transaction(cls):
        if _transaction is not None:
            _transaction.commit()
        _transaction = _connection.begin()

def execute(query, data=[]):
    _State.connection()
    _State.new_transaction()

    if data is None:
        data = []

    raise NotImplementedError()

    return {u'data': map(lambda row: map(dtos, row.values()), result),
        u'keys': result[0].keys()}

def select(query, data=None):
    _State.connection()
    _State.new_transaction()

    if data is None:
        data = []

    raise NotImplementedError()

    return result

def save(unique_keys, data, table_name=None):
    _State.connection()

    if table_name is not None:
        warnings.warn("scraperwiki.sql.save table_name is deprecated, \
                call scraperwiki.sql.set_table instead")
    else:
        table_name = _State.table_name

    raise NotImplementedError()

def set_table(table_name):
    _State.table_name = table_name

def show_tables():
    _State.connection()

    raise NotImplementedError()
    return {row['name']: row['sql'] for row in response}

def save_var(name, value):
    _State.connection()

    table_name = _State.table_name

    raise NotImplementedError()
    return data

def get_var(name, default=None):
    _State.connection()
    _State.new_transaction()

    table_name = _State.table_name

    raise NotImplementedError()
    return value

def commit():
    warnings.warn("scraperwiki.sql.commit is now a no-op")
