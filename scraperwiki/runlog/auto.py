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

        scraperwiki.runlog.write(filename, ''.join(traceback.format_tb(tb)),
            type_name, message, False)

        scraperwiki.status('error')
    finally:
        _inner_excepthook(type, value, tb)


sys.excepthook = sw_excepthook


@atexit.register
def successful_exit():
    if _successful_exit:

        filename = sys.argv[0]

        # Invoking a seperate process because sqlite breaks if run
        # during an atexit hook
        os.system(("python -c 'from sys import argv; "
            "import scraperwiki.runlog as R; "
            "R.write(argv[-1])' -- '{0}'")
            .format(filename))
