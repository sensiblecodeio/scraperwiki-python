#!/usr/bin/env python2
# utils.py
# David Jones, ScraperWiki Limited
# Thomas Levine, ScraperWiki Limited

'''
Local version of ScraperWiki Utils, documentation here:
https://scraperwiki.com/docs/python/python_help_documentation/
'''

import os
import warnings
import tempfile
import urllib, urllib2
 
def log(message=""):
    '''
    This is useful for profiling the code in the browser,
    but we just print the message in the local version
    '''
    print(message)

def httpresponseheader(headerkey, headervalue):
    '''
    Fake setting the HTTP Response Header.  For example
    scraperwiki.utils.httpresponseheader('Content-Type', 'text/plain')
    '''
    pass

def GET():
    '''
    This is deprecated. Also, it's useless if you're
    running locally rather than as a CGI script.
    '''
    warnings.warn('Deprecated', DeprecationWarning)   

def scrape (url, params = None, user_agent = None) :
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

def swimport(name, swinstance="https://scraperwiki.com"):
    'Import from a ScraperWiki script'
    url = "%s/editor/raw/%s" % (swinstance, name)
    os.system('wget -O %s.py \'%s\'' % (name, url))
    return __import__(name)

def jsviewcall(name, **args):
    'callback to a view with parameter lists (cross language capability)'
    url = "https://scraperwiki.com/views/%s/run/?%s" % (name, urllib.urlencode(args))
    response = urllib.urlopen(url).read()
    try:
        return json.loads(response)
    except ValueError:
        return response

urllib2opener = None
def urllibSetup(http_proxy):
    raise NotImplementedError('Dunno what this does')

class SWImporter(object):
    def __init__(self, swinstance="https://scraperwiki.com"):
        raise NotImplementedError('Standard Python imports are used instead')
