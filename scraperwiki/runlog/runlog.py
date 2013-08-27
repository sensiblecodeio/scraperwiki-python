"""
Special module, if you import this, you will get a run log written
to scraperwiki.sqlite in a table named _sw_runlog on succesful exits
or exceptions.
"""

import atexit
import datetime
import inspect
import os
import sys
import traceback

import scraperwiki

_successful_exit = True
_hook_installed = False

def make_excepthook(inner_excepthook):

    def sw_excepthook(type, value, tb):
        """Log uncaught exceptions to scraperwiki.sqlite file."""

        global _successful_exit
        _successful_exit = False

        try:
            first_frame_tuple = inspect.getouterframes(tb.tb_frame)[-1]
            (_frame, filename, _lineno, _where, _code, _) = first_frame_tuple
            
            type_name = type.__module__ + '.' + type.__name__

            message = repr(value)

            write_runlog(filename, ''.join(traceback.format_tb(tb)),
                type_name, message, False)

            scraperwiki.status('error')
        finally:
            inner_excepthook(type, value, tb)

    return sw_excepthook

def successful_exit():
    if _successful_exit:

        filename = sys.argv[0]

        # Invoking a seperate process because sqlite breaks if run
        # during an atexit hook
        os.system(("python -c 'from sys import argv; "
            "import scraperwiki.runlog as R; "
            "R.write_runlog(argv[-1])' -- '{0}'")
            .format(filename))

def write_runlog(filename, traceback="", exception_type="", exception_value="",
    success=True):

    d = dict(time=datetime.datetime.now(), path=filename, pwd=os.getcwd(),
        traceback=traceback, exception_type=exception_type,
        exception_value=exception_value,
        success=bool(success))

    scraperwiki.sql.save([], d, table_name="_sw_runlog")

def setup():
    """
    Initialize scraperwiki exception/success hook. Idempotent.
    """

    global _hook_installed
    if _hook_installed:
        return

    _hook_installed = True
    sys.excepthook = make_excepthook(sys.excepthook)
    atexit.register(successful_exit)
