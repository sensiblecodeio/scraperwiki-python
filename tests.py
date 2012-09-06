#!/usr/bin/env python2
from unittest import TestCase, main
from json import loads, dumps
import sqlite3
import os
import shutil
import datetime

import scraperwiki

# This library

class TestDb(TestCase):
  DBNAME = 'scraperwiki.sqlite'
  def setUp(self):
    self.cleanUp()
    scraperwiki.sqlite._connect(self.DBNAME)

  def tearDown(self):
    self.cleanUp()

  def cleanUp(self):
    "Clean up temporary files, then reinitialize."
    if self.DBNAME != ':memory:':
      try:
        os.remove(self.DBNAME)
      except OSError:
        pass

class SaveGetVar(TestDb):
  def savegetvar(self, var):
    scraperwiki.sqlite.save_var("weird", var)
    self.assertEqual(scraperwiki.sqlite.get_var("weird"), var)

class TestSaveGetList(SaveGetVar):
  def test_list(self):
    self.savegetvar([])

class TestSaveGetDict(SaveGetVar):
  def test_dict(self):
    self.savegetvar({})

class TestSaveVar(TestDb):
  def setUp(self):
    super(TestSaveVar, self).setUp()
    scraperwiki.sqlite.save_var("birthday","November 30, 1888")
    connection=sqlite3.connect(self.DBNAME)
    self.cursor=connection.cursor()

  def test_insert(self):
    self.cursor.execute("SELECT name, value_blob, type FROM `swvariables`")
    observed = self.cursor.fetchall()
    expected = [("birthday", "November 30, 1888", "text",)]
    self.assertEqual(observed, expected)

class TestSelect(TestDb):
  def test_select(self):
    shutil.copy('fixtures/landbank_branches.sqlite',self.DBNAME)
    scraperwiki.sqlite._connect(self.DBNAME)
    data_observed = scraperwiki.sqlite.select("* FROM `branches` WHERE Fax is not null ORDER BY Fax LIMIT 3;")
    data_expected = [{'town': u'\r\nCenturion', 'date_scraped': 1327791915.618461, 'Fax': u' (012) 312 3647', 'Tel': u' (012) 686 0500', 'address_raw': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 'blockId': 14, 'street-address': None, 'postcode': u'\r\n0001', 'address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', 'branchName': u'Head Office'}, {'town': u'\r\nCenturion', 'date_scraped': 1327792245.787187, 'Fax': u' (012) 312 3647', 'Tel': u' (012) 686 0500', 'address_raw': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 'blockId': 14, 'street-address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark', 'postcode': u'\r\n0001', 'address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', 'branchName': u'Head Office'}, {'town': u'\r\nMiddelburg', 'date_scraped': 1327791915.618461, 'Fax': u' (013) 282 6558', 'Tel': u' (013) 283 3500', 'address_raw': u'\r\n184 Jan van Riebeeck Street\n\r\nMiddelburg\n\r\n1050\n (013) 283 3500\n (013) 282 6558', 'blockId': 17, 'street-address': None, 'postcode': u'\r\n1050', 'address': u'\r\n184 Jan van Riebeeck Street\n\r\nMiddelburg\n\r\n1050', 'branchName': u'Middelburg'}]
    self.assertListEqual(data_observed, data_expected)

class TestShowTablesIterator(TestDb):
  def test_show_tables(self):
    shutil.copy('fixtures/landbank_branches.sqlite',self.DBNAME)
    scraperwiki.sqlite._connect(self.DBNAME)
    observed = set([name for name in scraperwiki.sqlite.show_tables()])
    expected = set(['blocks','branches'])
    self.assertSetEqual(observed, expected)

class TestShowTablesDict(TestDb):
  def test_show_tables(self):
    shutil.copy('fixtures/landbank_branches.sqlite', self.DBNAME)
    scraperwiki.sqlite._connect(self.DBNAME)
    observed = scraperwiki.sqlite.show_tables()
    expected = {
      'blocks': 'CREATE TABLE `blocks` (`blockPerson` text, `date_scraped` real, `region` text, `blockId` integer, `blockName` text)',
      'branches': 'CREATE TABLE `branches` (`town` text, `date_scraped` real, `Fax` text, `Tel` text, `address_raw` text, `blockId` integer, `postcode` text, `address` text, `branchName` text, `street-address` text)'
    }
    self.assertDictEqual(observed, expected)

class SaveAndCheck(TestDb):
  def save_and_check(self, dataIn, tableIn, dataOut, tableOut = None, twice = True):
    if tableOut == None:
      tableOut = '[' + tableIn + ']'

    # Insert
    scraperwiki.sqlite.save([], dataIn, tableIn)

    # Observe with pysqlite
    connection=sqlite3.connect(self.DBNAME)
    cursor=connection.cursor()
    cursor.execute("SELECT * FROM %s" % tableOut)
    observed1 = cursor.fetchall()
    connection.close()

    if twice:
      # Observe with DumpTruck
      observed2 = scraperwiki.sqlite.select('* FROM %s' % tableOut)
 
      #Check
      expected1 = dataOut
      expected2 = [dataIn] if type(dataIn) == dict else dataIn
 
      self.assertListEqual(observed1, expected1)
      self.assertListEqual(observed2, expected2)
      
class SaveAndSelect(TestDb):
  def save_and_select(self, d):
    scraperwiki.sqlite.save([], {"foo": d})

    observed = scraperwiki.sqlite.select('* from swdata')[0]['foo']
    self.assertEqual(d, observed)

class TestUniqueKeys(SaveAndSelect):
  def test_empty(self):
    scraperwiki.sqlite.save([], {"foo": 3}, u'Chico')
    observed = scraperwiki.sqlite.execute(u'PRAGMA index_list(Chico)')
    self.assertEqual(observed, {u'data': [], u'keys': []})

  def test_two(self):
    scraperwiki.sqlite.save(['foo', 'bar'], {"foo": 3, 'bar': 9}, u'Harpo')
    observed = scraperwiki.sqlite.execute(u'PRAGMA index_info(Harpo_foo_bar)')

    # Indexness
    self.assertIsNotNone(observed)

    # Indexed columns
    expected = {
      'keys': [u'seqno', u'cid', u'name'],
      'data':[
        [0, 0, u'foo'],
        [1, 1, u'bar'],
      ]
    }
    self.assertDictEqual(observed, expected)

    # Uniqueness
    indices = scraperwiki.sqlite.execute('PRAGMA index_list(Harpo)')
    namecol = indices[u"keys"].index(u'name')
    for index in indices[u"data"]:
      if index[namecol] == u'Harpo_foo_bar':
        break
    else:
      index = {}

    uniquecol = indices[u"keys"].index(u'unique')
    self.assertEqual(index[uniquecol], 1)

class TestSaveBoolean(SaveAndCheck):
  def test_save_true(self):
    self.save_and_check(
      {"a": True}
    , "a"
    , [(1,)]
    )

  def test_save_true(self):
    self.save_and_check(
      {"a": False}
    , "a"
    , [(0,)]
    )

class TestSaveTwice(SaveAndCheck):
  def test_save_twice(self):
    self.save_and_check(
      {"modelNumber": 293}
    , "model-numbers"
    , [(293,)]
    )
    self.save_and_check(
      {"modelNumber": 293}
    , "model-numbers"
    , [(293,), (293,)]
    , twice = False
    )

class TestSaveInt(SaveAndCheck):
  def test_save(self):
    self.save_and_check(
      {"modelNumber": 293}
    , "model-numbers"
    , [(293,)]
    )


class TestMultipleColumns(SaveAndSelect):
  def test_save(self):
    self.save_and_select({"firstname":"Robert","lastname":"LeTourneau"})

class TestSaveHyphen(SaveAndCheck):
  def test_save_int(self):
    self.save_and_check(
      {"model-number": 293}
    , "model-numbers"
    , [(293,)]
    )

class TestSaveString(SaveAndCheck):
  def test_save(self):
    self.save_and_check(
      {"lastname":"LeTourneau"}
    , "diesel-engineers"
    , [(u'LeTourneau',)]
    )

class TestSaveDate(SaveAndCheck):
  def test_save(self):
    self.save_and_check(
      {"birthday":datetime.datetime.strptime('1990-03-30', '%Y-%m-%d').date()}
    , "birthdays"
    , [(u'1990-03-30',)]
    )

class TestSaveDateTime(SaveAndCheck):
  def test_save(self):
    self.save_and_check(
      {"birthday":datetime.datetime.strptime('1990-03-30', '%Y-%m-%d')}
    , "birthdays"
    , [(u'1990-03-30 00:00:00',)]
    )

class TestAttach(TestDb):
  def hsph(self):
    #https://scraperwiki.com/scrapers/export_sqlite/hsph_faculty_1/
    scraperwiki.sqlite.attach('hsph_faculty_1')
    observed = scraperwiki.sqlite.select('count(*) as "c" from maincol')[0]['c']
    expected = 461
    self.assertEqual(observed, expected)

  def test_hsph1(self):
    "Do it normally"
    self.hsph()

  def test_hsph2(self):
    "Then corrupt the file and do it again"
    os.system('cat tests.py >> hsphfaculty')
    self.hsph()

  def setUp(self):
    super(TestAttach, self).setUp()
    os.system('rm hsphfaculty')

  def tearDown(self):
    super(TestAttach, self).tearDown()
    os.system('rm hsphfaculty')

class TestSWImport(TestCase):
  def test_csv2sw(self):
    csv2sw = scraperwiki.swimport('csv2sw')
    self.assertEquals(type(csv2sw.read.csv), type(lambda : None) )

class TestImports(TestCase):
  'Test that all module contents are imported.'
  def setUp(self):
    self.sw = __import__('scraperwiki')

  def test_import_scraperwiki_root(self):
    self.sw.scrape
    self.sw.Error
    self.sw.CPUTimeExceededError
    
  def test_import_scraperwiki_sqlite(self):
    self.sw.sqlite
    
  def test_import_scraperwiki_utils(self):
    self.sw.utils
    
  def test_import_scraperwiki_special_utils(self):
    self.sw.pdftoxml
    self.sw.dumpMessage
    
if __name__ == '__main__':
  main()
