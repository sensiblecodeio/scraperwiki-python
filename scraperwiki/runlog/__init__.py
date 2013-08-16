import atexit
import datetime
import inspect
import os
import sys
import traceback

import scraperwiki

_successful_exit = True

_inner_excepthook = sys.excepthook
def sw_excepthook(type, value, tb):
    """Log uncaught exceptions to scraperwiki.sqlite file."""

    global _successful_exit
    _successful_exit = False

    try:
        first_frame_tuple = inspect.getouterframes(tb.tb_frame)[-1]
        (_frame, filename, _lineno, _where, _code, _) = first_frame_tuple
        
        type_name = type.__module__ + '.' + type.__name__

        message = repr(value)
        
        d = dict(time=datetime.datetime.now(), path=filename, pwd=os.getcwd(),
            traceback=''.join(traceback.format_tb(tb)),
            exception_type=type_name, exception_value=message,
            success=False)

        scraperwiki.sql.save([], d, table_name="_sw_runlog")

        scraperwiki.status('error')
    finally:
        _inner_excepthook(type, value, tb)


sys.excepthook = sw_excepthook


@atexit.register
def successful_exit():
    if _successful_exit:
        d = dict(time=datetime.datetime.now(), path=filename, pwd=os.getcwd(),
            success=True)
        scraperwiki.sql.save([], d, table_name="_sw_runlog")
