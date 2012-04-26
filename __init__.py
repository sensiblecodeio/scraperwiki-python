
logfd = None # This does something on the hosted version

def dumpMessage(d):
    'This does something on the hosted version'
    print(d)

class Error(Exception):
    """All ScraperWiki exceptions are instances of this class
    (usually via a subclass)."""
    pass

class CPUTimeExceededError(Error):
    """CPU time limit exceeded."""
    pass

from utils import log, scrape, pdftoxml, swimport
