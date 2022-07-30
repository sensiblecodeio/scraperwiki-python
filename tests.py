#!/usr/bin/env python
from __future__ import absolute_import

import datetime
import json
import os
import re
import shutil
import sqlite3
import warnings

from subprocess import Popen, PIPE
from textwrap import dedent

from unittest import TestCase, main

import scraperwiki
import six

import sys
# scraperwiki.sql._State.echo = True
DB_NAME = 'scraperwiki.sqlite'

class Setup(TestCase):
    def test_setup(self):
        try:
            os.remove('scraperwiki.sqlite')
        except OSError:
            pass

class SaveAndSelect(TestCase):
    def save_and_select(self, d):
        scraperwiki.sql.save([], {u"foo\xdd": d})
        observed = scraperwiki.sql.select(u'* FROM swdata')[0][u'foo\xdd']
        self.assertEqual(d, observed)

class TestUniqueKeys(SaveAndSelect):
    def test_empty(self):
        scraperwiki.sql.save([], {u"foo\xde": 3}, table_name=u"Chico\xcc")
        observed = scraperwiki.sql.execute(u'PRAGMA index_list(Chico\xcc)')
        self.assertEqual(observed, {u'data': [], u'keys': []})

    def test_two(self):
        scraperwiki.sql.save([u'foo\xdc', u'bar\xcd'], {u'foo\xdc': 3, u'bar\xcd': 9}, u'Harpo\xbb')
        observed = scraperwiki.sql.execute(
            u'PRAGMA index_info(Harpo_foo_bar_unique)')

        # Indexness
        self.assertIsNotNone(observed)

        # Indexed columns
        expected1 = {
            u'keys': [u'seqno', u'cid', u'name'],
            u'data': [
                (0, 0, u'foo\xdc'),
                (1, 1, u'bar\xcd'),
            ]
        }
        expected2 = {
            u'keys': [u'seqno', u'cid', u'name'],
            u'data': [
                (0, 1, u'foo\xdc'),
                (1, 0, u'bar\xcd'),
            ]
        }
        try:
            self.assertDictEqual(observed, expected1)
        except Exception:
            self.assertDictEqual(observed, expected2)

        # Uniqueness
        indices = scraperwiki.sql.execute(u'PRAGMA index_list(Harpo\xbb)')
        namecol = indices[u"keys"].index(u'name')
        for index in indices[u"data"]:
            if index[namecol] == u'Harpo_foo_bar_unique':
                break
        else:
            index = {}

        uniquecol = indices[u"keys"].index(u'unique')
        self.assertEqual(index[uniquecol], 1)

if __name__ == '__main__':
    main()
