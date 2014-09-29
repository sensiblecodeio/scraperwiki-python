#!/usr/bin/env python

import datetime
import os
import re
import shutil
import sqlite3
import urllib2
import warnings

from subprocess import Popen, PIPE
from textwrap import dedent

from unittest import TestCase, main

import scraperwiki

# scraperwiki.sql._State.echo = True

DB_NAME = 'scraperwiki.sqlite'

class Setup(TestCase):
    def test_setup(self):
        try:
            os.remove('scraperwiki.sqlite')
        except OSError:
            pass


class TestException(TestCase):
    def testExceptionSaved(self):
        script = dedent("""
            import scraperwiki.runlog
            print scraperwiki.runlog.setup()
            raise ValueError
        """)
        process = Popen(["python", "-c", script],
                        stdout=PIPE, stderr=PIPE, stdin=open("/dev/null"))
        stdout, stderr = process.communicate()

        assert 'Traceback' in stderr, "stderr should contain the original Python traceback"
        match = re.match(r'^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', stdout)
        assert match, "runlog.setup() should return a run_id"

        l = scraperwiki.sql.select("""exception_type, run_id, time
          FROM _sw_runlog
          ORDER BY time DESC LIMIT 1""")

        # Check that some record is stored.
        assert l
        # Check that the exception name appears.
        assert 'ValueError' in l[0][
            'exception_type'], "runlog should save exception types to the database"
        # Check that the run_id from earlier has been saved.
        assert match.group() == l[0].get(
            'run_id'), "runlog should save a run_id to the database"
        # Check that the time recorded is relatively recent.
        time_str = l[0]['time']
        then = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
        assert (datetime.datetime.now() - then).total_seconds() < 5 * \
            60, "run log should save a time to the database"

    def testRunlogSuccess(self):
        script = dedent("""
            import scraperwiki.runlog
            print scraperwiki.runlog.setup()
        """)
        process = Popen(["python", "-c", script],
                        stdout=PIPE, stderr=PIPE, stdin=open("/dev/null"))
        stdout, stderr = process.communicate()

        l = scraperwiki.sql.select("""time, run_id, success
          FROM _sw_runlog
          ORDER BY time DESC LIMIT 1""")

        # Check that some record is stored.
        assert l
        # Check that it has saved a success column.
        assert l[0]['success']
        # Check that a run_id has been saved.
        match = re.match(r'^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', stdout)
        assert match.group() == l[0].get(
            'run_id'), "runlog should save a run_id to the database"
        # Check that the time is relatively recent.
        then = datetime.datetime.strptime(l[0]['time'], '%Y-%m-%d %H:%M:%S.%f')
        assert (datetime.datetime.now() - then).total_seconds() < 5 * 60

# called TestAAAWarning so that it gets run first by nosetests,
# which we need, otherwise the warning has already happened.
class TestAAAWarning(TestCase):
    def test_save_no_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            scraperwiki.sql.save(['id'], dict(id=4, tumble='weed'),
              table_name="warning_test")

class TestSaveGetVar(TestCase):
    def savegetvar(self, var):
        scraperwiki.sql.save_var("weird", var)
        self.assertEqual(scraperwiki.sql.get_var("weird"), var)

    def test_string(self):
        self.savegetvar("asdio")

    def test_int(self):
        self.savegetvar(1)

    def test_date(self):
        date1 = datetime.datetime.now()
        date2 = datetime.date.today()
        scraperwiki.sql.save_var("weird", date1)
        self.assertEqual(scraperwiki.sql.get_var("weird"), unicode(date1))
        scraperwiki.sql.save_var("weird", date2)
        self.assertEqual(scraperwiki.sql.get_var("weird"), unicode(date2))

    def test_save_multiple_values(self):
        scraperwiki.sql.save_var('foo', 'hello')
        scraperwiki.sql.save_var('bar', 'goodbye')

        self.assertEqual('hello', scraperwiki.sql.get_var('foo'))
        self.assertEqual('goodbye', scraperwiki.sql.get_var('bar'))

class TestGetNonexistantVar(TestCase):
    def test_get(self):
        self.assertIsNone(scraperwiki.sql.get_var('meatball'))

class TestSaveVar(TestCase):
    def setUp(self):
        super(TestSaveVar, self).setUp()
        scraperwiki.sql.save_var("birthday", "November 30, 1888")
        connection = sqlite3.connect(DB_NAME)
        self.cursor = connection.cursor()

    def test_insert(self):
        self.cursor.execute("""
          SELECT name, value_blob, type
          FROM `swvariables`
          WHERE name == "birthday"
          """)
        observed = self.cursor.fetchall()
        expected = [("birthday", "November 30, 1888", "text",)]
        ((a, b, c),) = observed
        observed = [(a, str(b), c)]
        self.assertEqual(observed, expected)

class SaveAndCheck(TestCase):
    def save_and_check(self, dataIn, tableIn, dataOut, tableOut=None, twice=True):
        if tableOut == None:
            tableOut = '[' + tableIn + ']'

        # Insert
        with scraperwiki.sql.Transaction():
            scraperwiki.sql.save([], dataIn, tableIn)

        # Observe with pysqlite
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM %s" % tableOut)
        observed1 = cursor.fetchall()
        connection.close()

        if twice:
            # Observe using this module
            observed2 = scraperwiki.sql.select('* FROM %s' % tableOut)

            # Check
            expected1 = dataOut
            expected2 = [dataIn] if type(dataIn) == dict else dataIn

            self.assertListEqual(observed1, expected1)
            self.assertListEqual(observed2, expected2)

class SaveAndSelect(TestCase):
    def save_and_select(self, d):
        scraperwiki.sql.save([], {"foo": d})
        observed = scraperwiki.sql.select('* FROM swdata')[0]['foo']
        self.assertEqual(d, observed)


class TestUniqueKeys(SaveAndSelect):
    def test_empty(self):
        scraperwiki.sql.save([], {"foo": 3}, table_name="Chico")
        observed = scraperwiki.sql.execute(u'PRAGMA index_list(Chico)')
        self.assertEqual(observed, {u'data': [], u'keys': []})

    def test_two(self):
        scraperwiki.sql.save(['foo', 'bar'], {'foo': 3, 'bar': 9}, u'Harpo')
        observed = scraperwiki.sql.execute(
            u'PRAGMA index_info(Harpo_foo_bar_unique)')

        # Indexness
        self.assertIsNotNone(observed)

        # Indexed columns
        expected = {
            u'keys': [u'seqno', u'cid', u'name'],
            u'data': [
                (0, 0, u'foo'),
                (1, 1, u'bar'),
            ]
        }
        self.assertDictEqual(observed, expected)

        # Uniqueness
        indices = scraperwiki.sql.execute('PRAGMA index_list(Harpo)')
        namecol = indices[u"keys"].index(u'name')
        for index in indices[u"data"]:
            if index[namecol] == u'Harpo_foo_bar_unique':
                break
        else:
            index = {}

        uniquecol = indices[u"keys"].index(u'unique')
        self.assertEqual(index[uniquecol], 1)

class TestSaveColumn(TestCase):
    def test_add_column(self):
        # Indicative for
        # https://github.com/scraperwiki/scraperwiki-python/issues/64

        # The bug is that in the first .save() of a process, a
        # new column cannot be added if the table already exists.
        # Because it's only the first .save() of a process, we
        # need to run a subprocess.
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE frigled (a TEXT);')
        cursor.execute('INSERT INTO frigled VALUES ("boo")')
        connection.close()

        script = dedent("""
          import scraperwiki
          scraperwiki.sql.save(['id'], dict(id=1, a="bar", b="foo"))
          """)
        process = Popen(["python", "-c", script],
                        stdout=PIPE, stderr=PIPE, stdin=open("/dev/null"))
        stdout, stderr = process.communicate()
        assert process.returncode == 0
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")


class TestSave(SaveAndCheck):
    def test_save_int(self):
        self.save_and_check(
            {"model-number": 293}, "model-numbers", [(293,)]
        )

    def test_save_string(self):
        self.save_and_check(
            {"lastname": "LeTourneau"}, "diesel-engineers", [
                (u'LeTourneau',)]
        )

    def test_save_twice(self):
        self.save_and_check(
            {"modelNumber": 293}, "modelNumbers", [(293,)]
        )
        self.save_and_check(
            {"modelNumber": 293}, "modelNumbers", [(293,), (293,)], twice=False
        )

    def test_save_true(self):
        self.save_and_check(
            {"a": True}, "true", [(1,)]
        )

    def test_save_false(self):
        self.save_and_check(
            {"a": False}, "false", [(0,)]
        )

    def test_save_table_name(self):
        """
        Test that after we use table_name= in one .save() a
        subsequent .save without table_name= uses the `swdata`
        table again.
        """
        scraperwiki.sql.save(['id'], dict(id=1, stuff=1),
          table_name='sticky')
        scraperwiki.sql.save(['id'], dict(id=2, stuff=2))
        results = scraperwiki.sql.select('* FROM sticky')
        self.assertEqual(1, len(results))
        (row, ) = results
        self.assertDictEqual(dict(id=1, stuff=1), row)

    def test_lxml_string(self):
        """Save lxml string."""

        import lxml.html

        # See https://github.com/scraperwiki/scraperwiki-python/issues/65

        # Careful, this looks like a string (eg, when printed or
        # repr()d), but is actually an instance of some class
        # internal to lxml.
        s = lxml.html.fromstring('<b>Hello</b>').xpath('//b')[0].text_content()
        self.save_and_check(
            {"text": s},
            "lxml",
            [(unicode(s),)]
        )

    def test_save_and_drop(self):
        scraperwiki.sql.save([], dict(foo=7), table_name="dropper")
        scraperwiki.sql.execute("DROP TABLE dropper")
        scraperwiki.sql.save([], dict(foo=9), table_name="dropper")

class TestQuestionMark(TestCase):
    def test_one_question_mark_with_nonlist(self):
        scraperwiki.sql.execute('CREATE TABLE zhuozi (a TEXT);')
        scraperwiki.sql.execute('INSERT INTO zhuozi VALUES (?)', 'apple')
        observed = scraperwiki.sql.select('* FROM zhuozi')
        self.assertListEqual(observed, [{'a': 'apple'}])
        scraperwiki.sql.execute('DROP TABLE zhuozi')

    def test_one_question_mark_with_list(self):
        scraperwiki.sql.execute('CREATE TABLE zhuozi (a TEXT);')
        scraperwiki.sql.execute('INSERT INTO zhuozi VALUES (?)', ['apple'])
        observed = scraperwiki.sql.select('* FROM zhuozi')
        self.assertListEqual(observed, [{'a': 'apple'}])
        scraperwiki.sql.execute('DROP TABLE zhuozi')

    def test_multiple_question_marks(self):
        scraperwiki.sql.execute('CREATE TABLE zhuozi (a TEXT, b TEXT);')
        scraperwiki.sql.execute(
            'INSERT INTO zhuozi VALUES (?, ?)', ['apple', 'banana'])
        observed = scraperwiki.sql.select('* FROM zhuozi')
        self.assertListEqual(observed, [{'a': 'apple', 'b': 'banana'}])
        scraperwiki.sql.execute('DROP TABLE zhuozi')


class TestDateTime(TestCase):
    def rawdate(self, table="swdata", column="datetime"):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute("SELECT {} FROM {}".format(column, table))
        rawdate = cursor.fetchall()[0][0]
        connection.close()
        return rawdate

    def test_save_date(self):
        d = datetime.datetime.strptime('1991-03-30', '%Y-%m-%d').date()
        with scraperwiki.sql.Transaction():
            scraperwiki.sql.save([], {"birthday": d})

            self.assertEqual(
                [{u'birthday': str(d)}],
                scraperwiki.sql.select("* FROM swdata"))

            self.assertEqual(
                {u'keys': [u'birthday'], u'data': [(unicode(d),)]},
                scraperwiki.sql.execute("SELECT * FROM swdata"))

        self.assertEqual(str(d), self.rawdate(column="birthday"))

    def test_save_datetime(self):
        d = datetime.datetime.strptime('1990-03-30', '%Y-%m-%d')
        with scraperwiki.sql.Transaction():
            scraperwiki.sql.save([], {"birthday": d},
              table_name="datetimetest")

            exemplar = unicode(d)
            # SQLAlchemy appears to convert with extended precision.
            exemplar += ".000000"

            self.assertEqual(
                [{u'birthday': exemplar}],
                scraperwiki.sql.select("* FROM datetimetest"))
            self.assertDictEqual(
                {u'keys': [u'birthday'], u'data': [(exemplar,)]},
                scraperwiki.sql.execute("SELECT * FROM datetimetest"))

        self.assertEqual(exemplar, self.rawdate(table="datetimetest", column="birthday"))

class TestStatus(TestCase):
    'Test that the status endpoint works.'

    def test_does_nothing_if_called_outside_box(self):
        scraperwiki.status('ok')

    def test_raises_exception_with_invalid_type_field(self):
        self.assertRaises(AssertionError, scraperwiki.status, 'hello')

    # XXX neeed some mocking tests for case of run inside a box


class TestImports(TestCase):

    'Test that all module contents are imported.'

    def setUp(self):
        self.sw = __import__('scraperwiki')

    def test_import_scraperwiki_root(self):
        self.sw.scrape

    def test_import_scraperwiki_sqlite(self):
        self.sw.sqlite

    def test_import_scraperwiki_sql(self):
        self.sw.sql

    def test_import_scraperwiki_status(self):
        self.sw.status

    def test_import_scraperwiki_utils(self):
        self.sw.utils

    def test_import_scraperwiki_special_utils(self):
        self.sw.pdftoxml

if __name__ == '__main__':
    main()
