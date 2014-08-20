from collections import Iterable, Mapping
from dumptruck import DumpTruck

import atexit
import datetime
import os
import re
import time
import sys


DATABASE_NAME = os.environ.get("SCRAPERWIKI_DATABASE_NAME", "scraperwiki.sqlite")
DATABASE_TIMEOUT = float(os.environ.get("SCRAPERWIKI_DATABASE_TIMEOUT", 300))

def _connect(dbname=DATABASE_NAME, timeout=DATABASE_TIMEOUT):
  'Initialize the database (again). This is mainly for testing'
  global dt
  dt = DumpTruck(dbname=dbname,
                 adapt_and_convert=False,
                 timeout=timeout)

_connect()

class _Buffer(object):
    """
    Buffer holds all state relating to scraperwiki.sqlite.save.

    The strategy is to buffer at most 50,000 records for at most 20 seconds.
    """
    # We measured O(0.5 seconds) between flushes with MAX_SIZE = 1000, so
    # don't penalize users who aren't hammering the system much more than this.
    MAX_SECONDS_BEFORE_FLUSH = 3

    # Measured to be a sweet spot with save_speedtest.py
    MAX_SIZE = 1000
    BAD_TYPE = "scraperwiki.sql.save requires mapping or iterable of mapping"

    buffered_saves = []
    buffered_table = None
    unique_keys = []
    flushing = False

    # time after which records should be automatically flushed.
    # It isn't a guarantee, but if the deadline is passed after an append,
    # then a flush will occur.
    flush_deadline = time.time() + MAX_SECONDS_BEFORE_FLUSH

    @classmethod
    def flush(cls):
        if cls.flushing:
            raise RuntimeError("Double flush")
            return

        cls.flushing = True

        if not cls.buffered_saves:
            cls.flushing = False
            return

        real_save(cls.unique_keys, cls.buffered_saves, cls.buffered_table)

        cls.unique_keys = None
        cls.buffered_table = None
        # In place list update to preserve other references to this list.
        cls.buffered_saves[:] = []

        cls.flush_deadline = time.time() + cls.MAX_SECONDS_BEFORE_FLUSH

        # It might be tempting to put this in a try-finally, but we *really*
        # aren't done until the above code has run.
        cls.flushing = False

    @classmethod
    def append(cls, unique_keys, data, table_name):
        if cls.unique_keys != unique_keys or cls.buffered_table != table_name:
            cls.flush()
        cls.unique_keys = unique_keys
        cls.buffered_table = table_name

        if isinstance(data, Mapping):
            cls.buffered_saves.append(data)
            if len(cls.buffered_saves) >= cls.MAX_SIZE:
                cls.flush()

        elif isinstance(data, Iterable):
            # Cache lookups
            buffered_saves = cls.buffered_saves
            append = cls.buffered_saves.append
            MAX_SIZE = cls.MAX_SIZE

            for datum in data:
                if not isinstance(datum, Mapping):
                    raise TypeError(cls.BAD_TYPE, type(datum))
                append(datum)
                if len(buffered_saves) >= MAX_SIZE:
                    cls.flush()
        else:
            # Not mapping or iterable of mapping
            raise TypeError(cls.BAD_TYPE, type(data))

        if cls.flush_deadline < time.time():
            # print "Flush deadline passed"
            cls.flush()

def flush():
    """
    Ensure that any buffered records are written out to sqlite
    """
    _Buffer.flush()

@atexit.register
def _finish():
    """
    Atexit handler to empty the buffer at process end
    """
    # print "Final buffer flush."

    if _Buffer.flushing:
        # The only way flushing can be true is if exit() is called during
        # flush(), in which case flushing won't work.
        return

    flush()

_ORIG_EXCEPTHOOK = sys.excepthook
def _excepthook(*args, **kwargs):
    # print "Flushing due to exception"
    if not _Buffer.flushing:
        flush()
    return _ORIG_EXCEPTHOOK(*args, **kwargs)
sys.excepthook = _excepthook

def execute(sqlquery, data=[], verbose=1):
    """ Emulate scraperwiki as much as possible by mangling dumptruck result """
    flush()

    # Allow for a non-list to be passed as data.
    if type(data) != list and type(data) != tuple:
        data = [data]

    result = dt.execute(sqlquery, data, commit=False)
    # None (non-select) and empty list (select) results
    if not result:
        return {u'data': [], u'keys': []}
    dtos = lambda d: str(d) if isinstance(d, datetime.date) else d
    # Select statement with results
    return {u'data': map(lambda row: map(dtos, row.values()), result),
            u'keys': result[0].keys()}

def save(unique_keys, data, table_name="swdata", verbose=2, date=None):
    if not data:
        return
    _Buffer.append(unique_keys, data, table_name)

def real_save(unique_keys, data, table_name="swdata", verbose=2, date=None):
    # print "Real save called, len(data) = {}".format(len(data))
    if not data:
        return
    dt.create_table(data, table_name = table_name, error_if_exists = False)
    if unique_keys != []:
        dt.create_index(unique_keys, table_name, unique = True, if_not_exists = True)
    return dt.upsert(data, table_name = table_name)

def commit(verbose=1):
    flush()
    dt.commit()

def select(sqlquery, data=[], verbose=1):
    flush()
    sqlquery = "select %s" % sqlquery   # maybe check if select or another command is there already?
    result = dt.execute(sqlquery, data, commit = False)
    # Convert dates to strings to conform to scraperwiki classic
    if result != []:
      keys = result[0].keys()
      for row in result:
        for key in keys:
          if isinstance(row[key], datetime.date):
            row[key] = str(row[key])
    return result

def show_tables(dbname=""):
    flush()
    name = "sqlite_master"
    if dbname:
        name = "`%s`.%s" % (dbname, name)
    response = select('name, sql from %s where type = "table";' % name)
    return {row['name']: row['sql'] for row in response}

def save_var(name, value, verbose=2):
    flush()
    data = dt.save_var(name, value)
    dt.execute(u"CREATE TABLE IF NOT EXISTS swvariables (`value_blob` blob, `type` text, `name` text PRIMARY KEY)", commit = False)
    dt.execute(u'INSERT OR REPLACE INTO swvariables SELECT `value`, `type`, `key` FROM `%s`' % dt._DumpTruck__vars_table, commit = False)
    dt.execute(u'DROP TABLE `%s`' % dt._DumpTruck__vars_table, commit = False)
    dt.commit()
    return data

def get_var(name, default=None, verbose=2):
    flush()
    if 'swvariables' not in show_tables(): # this should be unecessary
        return default
    dt.execute(u"CREATE TABLE IF NOT EXISTS swvariables (`value_blob` blob, `type` text, `name` text PRIMARY KEY)", commit = False)
    dt.execute(u"CREATE TEMPORARY TABLE IF NOT EXISTS %s (`value` blob, `type` text, `key` text PRIMARY KEY)" % dt._DumpTruck__vars_table, commit = False)

    sql = u'INSERT INTO `%s` (value, type, key) SELECT `value_blob`, `type`, `name` FROM `swvariables`' % dt._DumpTruck__vars_table
    dt.execute(sql, commit = False)
    try:
        value = dt.get_var(name)
    except NameError:
        dt.connection.rollback()
        return default
    dt.execute(u'DROP TABLE `%s`' % dt._DumpTruck__vars_table, commit = False)
    dt.commit()
    return value
