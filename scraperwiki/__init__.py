#!/usr/bin/env python
# Thomas Levine, ScraperWiki Limited

'''
Local version of ScraperWiki Utils, documentation here:
https://scraperwiki.com/docs/python/python_help_documentation/
'''
from __future__ import absolute_import

from .utils import scrape, pdftoxml, status
from . import utils
from . import sql

# Compatibility
sqlite = sql

class Error(Exception):
    """All ScraperWiki exceptions are instances of this class
    (usually via a subclass)."""
    pass

class CPUTimeExceededError(Error):
    """CPU time limit exceeded."""
    pass
