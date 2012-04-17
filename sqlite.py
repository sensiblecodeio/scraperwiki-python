import scraperwiki
from dumptruck import DumpTruck

dt = DumpTruck()

def execute(sqlquery, data=None, verbose=1):
    """ Should return list of lists, but returns list of dicts """
    return dt.execute(sqlquery, *data, commit=False)
    # other way [ dict(zip(result["keys"], d))  for d in result["data"] ]

def save(unique_keys, data, table_name="swdata", verbose=2, date=None):
    dt.create_table(data, table_name = table_name)
    #dt.add_index(unique_keys)
    return dt.insert(data, table_name = table_name)
   
def attach(name, asname=None, verbose=1):
    "This somehow connects to scraperwiki."
    raise NotImplementedError

def commit(verbose=1):
    dt.commit()

def select(sqlquery, data=None, verbose=1):
    sqlquery = "select %s" % sqlquery   # maybe check if select or another command is there already?
    return dt.execute(sqlquery, *data, commit = False)

def show_tables(dbname=""):
    return dt.tables()

def save_var(name, value, verbose=2):
    return dt.save_var(name, value)

def get_var(name, default=None, verbose=2):
    try:
        return dt.get_var(name)
    except NameError:
        return default
