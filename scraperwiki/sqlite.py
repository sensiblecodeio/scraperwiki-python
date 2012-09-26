from dumptruck import DumpTruck
import datetime
import re
import os

def _connect(dbname = 'scraperwiki.sqlite'):
  'Initialize the database (again). This is mainly for testing'
  global dt
  dt = DumpTruck(dbname = dbname)

_connect()

def execute(sqlquery, data=[], verbose=1):
    """ Emulate scraperwiki as much as possible by mangling dumptruck result """
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
    dt.create_table(data, table_name = table_name, error_if_exists = False)
    if unique_keys != []:
        dt.create_index(unique_keys, table_name, unique = True, if_not_exists = True)
    return dt.insert(data, table_name = table_name)

def attach(name, asname=None, verbose=1):
    "This somehow downloads the database from scraperwiki."
    if asname == None:
        asname = name
    os.system('wget -O %s https://scraperwiki.com/scrapers/export_sqlite/%s' % (asname, name))
    dt.execute('attach {0} AS {0}'.format(asname), commit = False)

def commit(verbose=1):
    dt.commit()

def select(sqlquery, data=[], verbose=1):
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
    name = "sqlite_master"
    if dbname:
        name = "`%s`.%s" % (dbname, name)
    response = select('name, sql from %s where type = "table";' % name)
    return {row['name']: row['sql'] for row in response}

def save_var(name, value, verbose=2):
    data = dt.save_var(name, value)
    dt.execute(u"CREATE TABLE IF NOT EXISTS swvariables (`value_blob` blob, `type` text, `name` text PRIMARY KEY)", commit = False)
    dt.execute(u'INSERT OR REPLACE INTO swvariables SELECT `value`, `type`, `key` FROM `%s`' % dt._DumpTruck__vars_table, commit = False)
    dt.execute(u'DROP TABLE `%s`' % dt._DumpTruck__vars_table, commit = False)
    dt.commit()
    return data

def get_var(name, default=None, verbose=2):
    if 'swvariables' not in show_tables():
        return default

    dt.execute(u"CREATE TABLE %s (`value` blob, `type` text, `key` text PRIMARY KEY)" % dt._DumpTruck__vars_table, commit = False)
    dt.execute(u'INSERT INTO %s SELECT `value_blob`, `type`, `name` FROM `swvariables`' % dt._DumpTruck__vars_table, commit = False)
    try:
        return dt.get_var(name)
    except NameError:
        dt.connection.rollback()
        return default
    else:
        dt.execute(u'DROP TABLE `%s`' % dt._DumpTruck__vars_table, commit = False)
        dt.commit()
