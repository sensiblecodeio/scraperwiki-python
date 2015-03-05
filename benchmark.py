#! /usr/bin/env python
from __future__ import absolute_import
import scraperwiki
import os
from six.moves import range

rows = [{'id': i, 'test': i * 2, 's': "abc"} for i in range(1000)]

try:
    os.remove('scraperwiki.sqlite')
except OSError:
    pass

scraperwiki.sql.save(['id'], rows)

for i, row in enumerate(rows):
    scraperwiki.sql.save(['id'], row)
