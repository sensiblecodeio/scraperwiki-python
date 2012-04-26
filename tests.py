#!/usr/bin/env python2
from unittest import TestCase, main
from json import loads, dumps
import sqlite
import sqlite3
import os
import shutil
import datetime
from dumptruck.convert import quote

class TestDb(TestCase):
  DBNAME = 'scraperwiki.db'
  def setUp(self):
    self.cleanUp()
    sqlite._connect(self.DBNAME)

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
    sqlite.save_var("weird", var)
    self.assertEqual(sqlite.get_var("weird"), var)

class TestSaveGetList(SaveGetVar):
  def test_list(self):
    self.savegetvar([])

class TestSaveGetDict(SaveGetVar):
  def test_dict(self):
    self.savegetvar({})

class TestSaveVar(TestDb):
  def setUp(self):
    super(TestSaveVar, self).setUp()
    sqlite.save_var("birthday","November 30, 1888")
    connection=sqlite3.connect(self.DBNAME)
    self.cursor=connection.cursor()

  def test_insert(self):
    self.cursor.execute("SELECT key, value, type FROM `_dumptruckvars`")
    observed = self.cursor.fetchall()
    expected = [("birthday", "November 30, 1888", "text",)]
    self.assertEqual(observed, expected)

class TestSelect(TestDb):
  def test_select(self):
    shutil.copy('dumptruck/fixtures/landbank_branches.sqlite',self.DBNAME)
    sqlite._connect(self.DBNAME)
    data_observed = sqlite.select("* FROM `branches` WHERE Fax is not null ORDER BY Fax LIMIT 3;")
    data_expected = [{'town': u'\r\nCenturion', 'date_scraped': 1327791915.618461, 'Fax': u' (012) 312 3647', 'Tel': u' (012) 686 0500', 'address_raw': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 'blockId': 14, 'street-address': None, 'postcode': u'\r\n0001', 'address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', 'branchName': u'Head Office'}, {'town': u'\r\nCenturion', 'date_scraped': 1327792245.787187, 'Fax': u' (012) 312 3647', 'Tel': u' (012) 686 0500', 'address_raw': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001\n (012) 686 0500\n (012) 312 3647', 'blockId': 14, 'street-address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark', 'postcode': u'\r\n0001', 'address': u'\r\n420 Witch Hazel Ave\n\r\nEcopark\n\r\nCenturion\n\r\n0001', 'branchName': u'Head Office'}, {'town': u'\r\nMiddelburg', 'date_scraped': 1327791915.618461, 'Fax': u' (013) 282 6558', 'Tel': u' (013) 283 3500', 'address_raw': u'\r\n184 Jan van Riebeeck Street\n\r\nMiddelburg\n\r\n1050\n (013) 283 3500\n (013) 282 6558', 'blockId': 17, 'street-address': None, 'postcode': u'\r\n1050', 'address': u'\r\n184 Jan van Riebeeck Street\n\r\nMiddelburg\n\r\n1050', 'branchName': u'Middelburg'}]
    self.assertListEqual(data_observed, data_expected)

class TestShowTables(TestDb):
  def test_show_tables(self):
    shutil.copy('dumptruck/fixtures/landbank_branches.sqlite',self.DBNAME)
    sqlite._connect(self.DBNAME)
    self.assertSetEqual(sqlite.show_tables(),set(['blocks','branches']))

class SaveAndCheck(TestDb):
  def save_and_check(self, dataIn, tableIn, dataOut, tableOut = None, twice = True):
    if tableOut == None:
      tableOut = quote(tableIn)

    # Insert
    sqlite.save([], dataIn, tableIn)

    # Observe with pysqlite
    connection=sqlite3.connect(self.DBNAME)
    cursor=connection.cursor()
    cursor.execute("SELECT * FROM %s" % tableOut)
    observed1 = cursor.fetchall()
    connection.close()

    if twice:
      # Observe with DumpTruck
      observed2 = sqlite.select('* FROM %s' % tableOut)
 
      #Check
      expected1 = dataOut
      expected2 = [dataIn] if type(dataIn) == dict else dataIn
 
      self.assertListEqual(observed1, expected1)
      self.assertListEqual(observed2, expected2)
      

class TestSaveDict(SaveAndCheck):
  def test_save_integers(self):
    d = {1: "A", 2: "B", 3: "C"}
    self.assertRaises(TypeError, lambda: self.save_and_check(
      {"modelNumber": d}
    , "model-numbers"
    , [(dumps(d),)]
    ))

  def test_save_text(self):
    d = {'1': 'A', '2': 'B', '3': 'C'}
    self.save_and_check(
      {"modelNumber": d}
    , "model-numbers"
    , [(dumps(d),)]
    )

  def test_save_fanciness(self):
    d = {'1': datetime.datetime(2012, 3, 5)}
    self.assertRaises(TypeError, lambda: self.save_and_check(
      {"modelNumber": d}
    , "model-numbers"
    , [(dumps(d),)]
    ))

class SaveAndSelect(TestDb):
  def save_and_select(self, d):
    sqlite.save([], {"foo": d})

    observed = sqlite.select('* from swdata')[0]['foo']
    self.assertEqual(d, observed)

#class TestSaveLambda(SaveAndSelect):
#  def test_save_lambda(self):
#    self.save_and_select(lambda x: x^2)

class TestSaveSet(SaveAndSelect):
  def test_save_set(self):
    self.save_and_select(set(["A", "B", "C"]))

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

class TestSaveList(SaveAndCheck):
  def test_save_integers(self):
    d = ["A", "B", "C"]
    self.save_and_check(
      {"model-codes": d}
    , "models"
    , [(dumps(d),)]
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

class TestSaveWeirdTableName1(SaveAndCheck):
  def test_save(self):
    self.save_and_check(
      {"modelNumber": 293}
    , "This should-be a_valid.table+name!?"
    , [(293,)]
    )

class TestSaveWeirdTableName2(SaveAndCheck):
  def test_save(self):
    self.save_and_check(
      {"lastname":"LeTourneau"}
    , "`asoeu`"
    , [(u'LeTourneau',)]
    )

class TestSaveWeirdTableName3(SaveAndCheck):
  def test_save(self):
    self.save_and_check(
      {"lastname":"LeTourneau"}
    , "[asoeu]"
    , [(u'LeTourneau',)]
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
    sqlite.attach('hsph_faculty_1')
    observed = sqlite.select('count(*) as "c" from maincol')[0]['c']
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

if __name__ == '__main__':
  main()
