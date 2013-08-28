#!/usr/bin/env python2
# utils.py
# David Jones, ScraperWiki Limited
# Thomas Levine, ScraperWiki Limited

'''
Local version of ScraperWiki Utils, documentation here:
https://scraperwiki.com/docs/python/python_help_documentation/
'''

import os
import sys
import warnings
import tempfile
import urllib, urllib2
import requests

def scrape(url, params = None, user_agent = None) :
    '''
    Scrape a URL optionally with parameters.
    This is effectively a wrapper around urllib2.orlopen.
    '''

    headers = {}

    if user_agent:
        headers['User-Agent'] = user_agent

    data = params and urllib.urlencode(params) or None
    req = urllib2.Request(url, data=data, headers=headers)
    f = urllib2.urlopen(req)

    text = f.read()
    f.close()

    return text

def pdftoxml(pdfdata):
    """converts pdf file to xml file"""
    pdffout = tempfile.NamedTemporaryFile(suffix='.pdf')
    pdffout.write(pdfdata)
    pdffout.flush()

    xmlin = tempfile.NamedTemporaryFile(mode='r', suffix='.xml')
    tmpxml = xmlin.name # "temph.xml"
    cmd = 'pdftohtml -xml -nodrm -zoom 1.5 -enc UTF-8 -noframes "%s" "%s"' % (pdffout.name, os.path.splitext(tmpxml)[0])
    cmd = cmd + " >/dev/null 2>&1" # can't turn off output, so throw away even stderr yeuch
    os.system(cmd)

    pdffout.close()
    #xmlfin = open(tmpxml)
    xmldata = xmlin.read()
    xmlin.close()
    return xmldata

def _in_box():
  return os.path.isfile(os.path.expanduser("~/box.json"))

def status(type, message=None):
    assert type in ['ok', 'error']

    # if not running in a ScraperWiki platform box, silently do nothing
    if not _in_box():
        return "Not in box"

    url = os.environ.get("SW_STATUS_URL", "https://scraperwiki.com/api/status")
    if url == "OFF":
        # For development mode
        return

    # send status update to the box
    r = requests.post(url, data={'type':type, 'message':message})
    r.raise_for_status()
    return r.content




