import datetime
import inspect
import os
import sys
import traceback

import scraperwiki

_inner_excepthook = sys.excepthook
def sw_excepthook(type, value, tb):
    """Log uncaught exceptions to scraperwiki.sqlite file."""

    try:
        first_frame_tuple = inspect.getouterframes(tb.tb_frame)[-1]
        (_frame, filename, _lineno, _where, _code, _) = first_frame_tuple
        
        type_name = type.__module__ + '.' + type.__name__
        
        d = dict(time=datetime.datetime.now(), path=filename,
          traceback=''.join(traceback.format_tb(tb)),
          pwd=os.getcwd(), exception_type=type_name, exception_value=repr(value))

        scraperwiki.sql.save([], d, table_name="_sw_error")
    finally:
        _inner_excepthook(type, value, tb)


sys.excepthook = sw_excepthook
