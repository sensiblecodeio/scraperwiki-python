#!/usr/bin/env python2

# This file is part of Local Scraperlibs.

# Local Scraperlibs is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Local Scraperlibs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.

# You should have received a copy of the GNU Affero Public License
# along with Local Scraperlibs.  If not, see <http://www.gnu.org/licenses/>.

import os
from distutils.core import setup
import scraperwiki

def has_external_dependency(name):
    'Check that a non-Python dependency is installed.'
    for directory in os.environ['PATH'].split(':'):
        if os.path.exists(os.path.join(directory, name)):
            return True
    return False

if not has_external_dependency('wget'):
    raise ImportError(
        'Local Scraperlibs requires wget because I\'m sloppy, but wget was not\n'
        'found in the PATH. You probably need to install it.'
    )

if not has_external_dependency('pdftohtml'):
    raise ImportError(
        'Local Scraperlibs requires pdftohtml, but pdftoxml was not found\n'
        'in the PATH. You probably need to install it.'
    )

setup(name='scraperwiki_local',
    author='Thomas Levine',
    author_email='thomas@scraperwiki.com',
    description='Local version of scraperwiki scraperlibs',
    url='https://github.com/tlevine/scraperwiki_local',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: SQL',
        'Topic :: Database :: Front-Ends',
    ],
    packages=['scraperwiki'],

    # From requests
    version=scraperwiki.__version__,
    license='AGPL',
   )
