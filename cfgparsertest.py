# -----------------------------------------------------------------------------
# cfgparsertest -- tests for the cfgparser module
# Copyright 2014, Ensoft Ltd
# -----------------------------------------------------------------------------

import cfgparser
import unittest
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

_example_file = """
[evalvals]
val1 = 42
val2 = this is a string
val3 = this is a string
  across multiple lines
val4 = True
val5 = off
val6 = true
val7 = yes
val8 = no
val9 = on
val10 = [1, 5, "hello"]
val11 = 4.2
val12 = {1: 0, 5: 0, "hello": 0}
val13 = {1: 12, 5: "hello",
  "bye": ["a", "b", 3]}
val14 = None

[listvals]
val1 = hello
val2 = hello, there, comma, list
val3 = this
  list
  uses
  newlines
val4 = now, lets, combine,
  the, two, together
val5 = 1, 2, 3, None, no, yes

[command: foo]
dir = bar

[ Command:    bar ]
dir = baz
[CoMmaNd:baz]
dir:quux

[results: hello]
type = add
"""

class EvaluatedValuesTest(unittest.TestCase):
    def setUp(self):
        self.cfg = cfgparser.CfgParser()
        self.cfg.readfp(StringIO(_example_file))

    def test_configsectionhelper(self):
        s = self.cfg.section("bar", category="command")
        self.assertEqual(s.options(), ["dir"])
        self.assertFalse(s.has_option("blahblah"))
        self.assertEqual(s.get("dir"), "baz")
        self.assertEqual(s.items(), [("dir", "baz")])
        s = self.cfg.section("listvals")
        self.assertEqual(s.get("val1"), "hello")
        self.assertEqual(len(s.getlist("val5", evaluate=True)), 6)
        s = self.cfg.section("evalvals")
        self.assertEqual(s.geteval("val11"), 4.2)

    def test_categories(self):
        self.assertEqual(list(self.cfg.categories()), ["command", "results"])
        self.assertEqual(list(self.cfg.sections("command")),
                         ["foo", "bar", "baz"])
        self.assertEqual(self.cfg.get("foo", "dir", category="command"), "bar")
        self.assertEqual(len(self.cfg.sections()), 6)
        self.assertTrue(self.cfg.has_section("evalvals"))
        self.assertTrue(self.cfg.has_section("bar", category="command"))
        self.assertFalse(self.cfg.has_section("bye", category="results"))
        self.assertFalse(self.cfg.has_section("bye", category="nonexistentcategory"))
        self.assertEqual(self.cfg.options("foo", category="command"), ["dir"])
        self.assertEqual(len(self.cfg.options("listvals")), 5)
        self.assertTrue(self.cfg.has_option("baz", "dir", category="command"))
        self.assertTrue(self.cfg.has_option("listvals", "val3"))
        self.assertEqual(self.cfg.items("hello", category="results"),
                         [("type", "add")])
        self.assertEqual(len(self.cfg.items("listvals")), 5)

    def _checklen(self, field, num):
        self.assertEqual(len(self.cfg.getlist("listvals", field)), num)

    def test_listlens(self):
        self._checklen("val1", 1)
        self._checklen("val2", 4)
        self._checklen("val3", 4)
        self._checklen("val4", 6)
        self._checklen("val5", 6)

    def test_listvals(self):
        v = self.cfg.getlist("listvals", "val4")
        for i in v:
            self.assertFalse(',' in i)
        v = self.cfg.getlist("listvals", "val5", evaluate=True)
        self.assertEqual(v, [1, 2, 3, None, False, True])

    def _checktype(self, field, typ):
        self.assertIsInstance(self.cfg.geteval("evalvals", field), typ)
         
    def test_evalvals(self):
        self._checktype("val1", int)
        self._checktype("val2", str)
        self._checktype("val3", str)
        self._checktype("val4", bool)
        self._checktype("val5", bool)
        self._checktype("val10", list)
        self._checktype("val11", float)
        self._checktype("val12", dict)
        self._checktype("val13", dict)

    def _checkval(self, field, val):
        self.assertEqual(self.cfg.geteval("evalvals", field), val)

    def test_bools(self):
        self._checkval("val5", False)
        self._checkval("val6", True)
        self._checkval("val7", True)
        self._checkval("val8", False)
        self._checkval("val9", True)
        self._checkval("val14", None)

if __name__ == '__main__':
    unittest.main()
