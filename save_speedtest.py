#! /usr/bin/env python2
import scraperwiki
from time import time

rows = [{'id': i, 'test': i * 2, 's': "xx"*i} for i in xrange(10)]

def test_buffer_size(n):

	start = time()

	scraperwiki.sql._Buffer.MAX_SIZE = n
	for i, row in enumerate(rows):
		scraperwiki.sql.save(['id'], row)
	scraperwiki.sql.flush()

	delta = time() - start
	print "Took {:.3f} for bufsize = {} ({:.1f} / sec)".format(delta, n, len(rows) / delta)

# for size in [3, 10, 30, 100, 300, 1000, 10000]:
# 	test_buffer_size(size)

# from time import sleep


for i, row in enumerate(rows):
	scraperwiki.sql.save(['id'], row)