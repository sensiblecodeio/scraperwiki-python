#! /usr/bin/env python2
import scraperwiki

rows = [{'id': i, 'test': i * 2, 's': "xx"*i} for i in xrange(10)]

for i, row in enumerate(rows):
	scraperwiki.sql.save(['id'], row)
