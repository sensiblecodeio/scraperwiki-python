import datetime
import os

import scraperwiki

def write(filename, traceback="", exception_type="", exception_value="",
	success=True):

    d = dict(time=datetime.datetime.now(), path=filename, pwd=os.getcwd(),
        traceback=traceback, exception_type=exception_type,
        exception_value=exception_value,
        success=bool(success))

    scraperwiki.sql.save([], d, table_name="_sw_runlog")
