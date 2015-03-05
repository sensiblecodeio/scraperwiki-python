#! /usr/bin/env python
from __future__ import absolute_import
import scraperwiki
from six.moves import range

rows = [{'id': i, 'test': i * 2, 's': "xx"*i} for i in range(10)]

for i, row in enumerate(rows):
	scraperwiki.sql.save(['id'], row)
