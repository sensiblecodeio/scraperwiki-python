#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
import os
import sys
import urllib
from optparse import OptionParser

USAGE = "usage: %prog <scrapername>"
DESCRIPTION = """
This script will allow you to retrieve the data and code from a scraper
you previously wrote on ScraperWiki classic.  It requires a username
and a scraper name and will attempt to download the relevant data to
your machine
"""

def _bail(message):
    print >>sys.stderr, message
    sys.exit(1)

def _ensure_dir(f):
    if not f:
        return
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def export():
    # Quick and easy usage/description and -h handling
    parser = OptionParser(usage=USAGE, description=DESCRIPTION)
    parser.add_option("-c", "--codefile",
                      type="string", dest="codefile")    
    parser.add_option("-d", "--dbfile",
                      type="string", dest="dbfile")        
    (options, args) = parser.parse_args()

    if not options.codefile or not options.dbfile:
        parser.error("You must provide both the codefile option and the dbfile option")

    if not args:
        parser.error("You need to provide a scraper short name from ScraperWiki classic")

    # Build/hard-code the URLs we'll use
    db_address = "https://scraperwiki.com/scrapers/export_sqlite/%s/" % args[0]
    code_address = "https://api.scraperwiki.com/api/1.0/scraper/getinfo?format=jsondict&"\
        "name={s}&version=-1&quietfields=history%7Cdatasummary%7Cuserroles%7Crunevents".format(s=args[0])

    codefile = os.path.abspath(options.codefile)
    dbfile   = os.path.abspath(options.dbfile)
    _ensure_dir(codefile)
    _ensure_dir(dbfile)

    # Get info about the file
    r = requests.get(code_address)
    if r.status_code != 200:
        _bail("Failed to get information about the scraper - is the name correct?")
    info = json.loads(r.content)
    with open(codefile, 'wb') as f:
        f.write(info[0]['code'])
    
    urllib.urlretrieve(db_address, dbfile)