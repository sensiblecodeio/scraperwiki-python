#!/usr/bin/env python2
from unittest import TestCase, main
from json import loads, dumps
import sqlite3
import os
import shutil
import datetime
import urllib2

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

class TestSaveGetVar(TestDb):
  def savegetvar(self, var):
    scraperwiki.sqlite.save_var("weird", var)
    self.assertEqual(scraperwiki.sqlite.get_var("weird"), var)

  def test_string(self):
    self.savegetvar("asdio")
  
  def test_int(self):
    self.savegetvar(1)

  def test_list(self):
    self.savegetvar([1,2,3,4])

  def test_dict(self):
    self.savegetvar({"abc":"def"})

  def test_date(self):
    date1 = datetime.datetime.now()
    date2 = datetime.date.today()
    scraperwiki.sqlite.save_var("weird", date1)
    self.assertEqual(scraperwiki.sqlite.get_var("weird"), date1)
    scraperwiki.sqlite.save_var("weird", date2)
    self.assertEqual(scraperwiki.sqlite.get_var("weird"), date2)

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

class TestCommands(TestDb):
  def setUp(self):
    shutil.copy('fixtures/landbank_branches.sqlite',self.DBNAME)
    scraperwiki.sqlite._connect(self.DBNAME)

  def test_select(self):
    data_observed = scraperwiki.sqlite.select("* FROM `branches` WHERE Fax is not null ORDER BY Fax LIMIT 2;")
    data_expected = [{'town': u'\r\nCenturion', 'date_scraped': 1327791915.618461, 'Fax': u' (012) 312 3647', 'Tel': u' (012) 686 0500', 'address_raw': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 'blockId': 14, 'street-address': None, 'postcode': u'\r\n0001', 'address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', 'branchName': u'Head Office'}, {'town': u'\r\nCenturion', 'date_scraped': 1327792245.787187, 'Fax': u' (012) 312 3647', 'Tel': u' (012) 686 0500', 'address_raw': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 'blockId': 14, 'street-address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark', 'postcode': u'\r\n0001', 'address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', 'branchName': u'Head Office'}] 
    self.assertListEqual(data_observed, data_expected)

  def test_execute(self):
    data_observed = scraperwiki.sqlite.execute("SELECT * FROM `branches` WHERE Fax is not null ORDER BY Fax LIMIT 2;")
    self.assertEqual(data_observed, {u'keys': [u'town', u'date_scraped', u'Fax', u'Tel', u'address_raw', u'blockId', u'postcode', u'address', u'branchName', u'street-address'], u'data': [[u'\r\nCenturion', 1327791915.618461, u' (012) 312 3647', u' (012) 686 0500', u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 14, u'\r\n0001', u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', u'Head Office', None], [u'\r\nCenturion', 1327792245.787187, u' (012) 312 3647', u' (012) 686 0500', u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 14, u'\r\n0001', u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', u'Head Office', u'\r\n420 Witch Hazel Ave\n\r\nEcopark']]})

  def test_select_data(self):
    data_observed = scraperwiki.sqlite.select("date_scraped FROM `branches` WHERE Fax=? AND date_scraped=?", [u" (012) 312 3647", 1327792245.787187])
    self.assertEqual(data_observed, [{u'date_scraped': 1327792245.787187}]) 

  def test_execute_data(self):
    scraperwiki.sqlite.execute("INSERT INTO `branches` VALUES (?,?,?,?,?,?,?,?,?,?)", ["sometown",2,3,4,5,6,7,8,9,0])
    data_observed = scraperwiki.sqlite.execute("SELECT * FROM `branches` WHERE TOWN=?", ["sometown"])
    self.assertEqual(data_observed, {u'keys': [u'town', u'date_scraped', u'Fax', u'Tel', u'address_raw', u'blockId', u'postcode', u'address', u'branchName', u'street-address'], u'data': [[u'sometown', 2.0, u'3', u'4', u'5', 6, u'7', u'8', u'9', u'0']]})

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

class TestMultipleColumns(SaveAndSelect):
  def test_save(self):
    self.save_and_select({"firstname":"Robert","lastname":"LeTourneau"})

class TestSave(SaveAndCheck):
  def test_save_int(self):
    self.save_and_check(
      {"model-number": 293}
    , "model-numbers"
    , [(293,)]
    )

  def test_save_string(self):
    self.save_and_check(
      {"lastname":"LeTourneau"}
    , "diesel-engineers"
    , [(u'LeTourneau',)]
    )

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

class TestDateTime(TestDb):

  def rawdate(self, table="swdata", column="datetime"):
    connection=sqlite3.connect(self.DBNAME)
    cursor=connection.cursor()
    cursor.execute("SELECT %s FROM %s LIMIT 1" % (column, table))
    rawdate = cursor.fetchall()[0][0]
    connection.close()
    return rawdate
   
  def test_save_date(self):
    d = datetime.datetime.strptime('1990-03-30', '%Y-%m-%d').date()
    scraperwiki.sqlite.save([], {"birthday":d})
    self.assertEqual(str(d), self.rawdate(column="birthday"))
    self.assertEqual([{u'birthday':str(d)}], scraperwiki.sqlite.select("* from swdata"))
    self.assertEqual({u'keys': [u'birthday'], u'data': [[str(d)]]}, scraperwiki.sqlite.execute("select * from swdata"))

  def test_save_datetime(self):
    d = datetime.datetime.strptime('1990-03-30', '%Y-%m-%d')
    scraperwiki.sqlite.save([], {"birthday":d})
    self.assertEqual(str(d), self.rawdate(column="birthday"))
    self.assertEqual([{u'birthday':str(d)}], scraperwiki.sqlite.select("* from swdata"))
    self.assertEqual({u'keys': [u'birthday'], u'data': [[str(d)]]}, scraperwiki.sqlite.execute("select * from swdata"))

class TestSWImport(TestCase):
  def test_csv2sw(self):
    csv2sw = scraperwiki.swimport('csv2sw')
    self.assertEquals(type(csv2sw.read.csv), type(lambda : None) )

class TestGeo(TestCase):

  postcodes = ["M15 4JY","bB8 9ex","l35uf"]

  def check_postcode_to_latlng(self, postcode):
    (lat, lng) = scraperwiki.geo.gb_postcode_to_latlng(postcode)
    resp = loads(scraperwiki.scrape('http://mapit.mysociety.org/postcode/%s.json' % urllib2.quote(postcode)))
    # For the UK a precision of 3dp (0.001) gives a latitude error
    # of ~110m and longitude ~60m
    self.assertEqual(round(lat, 3), round(resp['wgs84_lat'], 3))
    self.assertEqual(round(lng, 3), round(resp['wgs84_lon'], 3))

  def check_easting_northing_to_latlng(self, postcode):
    resp = loads(scraperwiki.scrape('http://mapit.mysociety.org/postcode/%s.json' % urllib2.quote(postcode)))
    (lat, lng) = scraperwiki.geo.os_easting_northing_to_latlng(resp['easting'], resp['northing'])
    # For the UK a precision of 5dp (0.00001) gives a latitude error
    # of ~1m and longitude ~0.5m
    self.assertEqual(round(lat, 5), round(resp['wgs84_lat'], 5))
    self.assertEqual(round(lng, 5), round(resp['wgs84_lon'], 5))

  def test_postcode_to_latlng(self):
    map(self.check_postcode_to_latlng, self.postcodes)

  def test_easting_northing_to_latlng(self):
    map(self.check_easting_northing_to_latlng, self.postcodes)

  def test_extract_gb_postcode(self):
    self.assertEqual(
      map(scraperwiki.geo.extract_gb_postcode,
          ["21 Golf Road, SWANLAWS, Td8 5tw", 
           "41 Ilchester Road, MUIRHOUSES, EH519YR"]),
      ["Td8 5tw", "EH519YR"])

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
    
  def test_import_scraperwiki_geo(self):
    self.sw.geo
    
  def test_import_scraperwiki_utils(self):
    self.sw.utils
    
  def test_import_scraperwiki_special_utils(self):
    self.sw.pdftoxml
    self.sw.dumpMessage
    
if __name__ == '__main__':
  main()
