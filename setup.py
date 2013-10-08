#!/usr/bin/env python2

# This file is part of Local Scraperlibs.

import warnings
import os
from distutils.core import setup

def has_external_dependency(name):
    'Check that a non-Python dependency is installed.'
    for directory in os.environ['PATH'].split(':'):
        if os.path.exists(os.path.join(directory, name)):
            return True
    return False

if not has_external_dependency('pdftohtml'):
    warnings.warn(
        'Local Scraperlibs requires pdftohtml, but pdftohtml was not found\n'
        'in the PATH. You probably need to install it.'
    )

config = dict(name='scraperwiki',
    author='Francis Irving',
    author_email='francis@scraperwiki.com',
    description='Local version of ScraperWiki libraries',
    url='https://github.com/scraperwiki/scraperwiki-python',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: SQL',
        'Topic :: Database :: Front-Ends',
    ],
    packages=['scraperwiki', 'scraperwiki.runlog'],

    version = '0.3.7',
    license='GPL',
   )

try:
    from setuptools import setup
    config['install_requires'] = ['dumptruck>=0.1.2', 'requests'],
except ImportError:
    pass

setup(**config)
