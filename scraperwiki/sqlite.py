from dumptruck import DumpTruck
import re
import os

def _connect(dbname = 'scraperwiki.db'):
  'Initialize the database (again). This is mainly for testing'
  global dt
  dt = DumpTruck(dbname = dbname)

_connect()

def execute(sqlquery, data=[], verbose=1):
    """ Should return list of lists, but returns list of dicts """
    return dt.execute(sqlquery, *data, commit=False)
    # other way [ dict(zip(result["keys"], d))  for d in result["data"] ]

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
        asname = re.sub(r'[^a-zA-Z]', '', name)
    os.system('wget -O %s https://scraperwiki.com/scrapers/export_sqlite/%s' % (asname, name))
    dt.execute('attach {0} AS {0}'.format(asname), commit = False)

def commit(verbose=1):
    dt.commit()

def select(sqlquery, data=None, verbose=1):
    sqlquery = "select %s" % sqlquery   # maybe check if select or another command is there already?
    if data == None:
        return dt.execute(sqlquery, commit = False)
    else:
        raise NotImplementedError('Dunno what that data argument does')

def show_tables(dbname=""):
    if dbname != '':
        raise NotImplementedError('Only the main database is implemented')
    response = select('name, sql from sqlite_master where type = "table";')
    return {row['name']: row['sql'] for row in response}

def save_var(name, value, verbose=2):
    return dt.save_var(name, value)

def get_var(name, default=None, verbose=2):
    try:
        return dt.get_var(name)
    except NameError:
        return default
