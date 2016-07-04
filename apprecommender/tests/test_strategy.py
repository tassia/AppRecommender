#!/usr/bin/env python
"""
    strategyTests - Recommendation strategies classes test case
"""
__author__ = "Tassia Camoes Araujo <tassia@gmail.com>"
__copyright__ = "Copyright (C) 2011 Tassia Camoes Araujo"
__license__ = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import unittest
import xapian

from apprecommender.decider import (PkgMatchDecider, PkgExpandDecider,
                                    TagExpandDecider)


class PkgMatchDeciderTests(unittest.TestCase):

    def setUp(self):
        pkgs_list = ["gimp", "eog", "inkscape"]
        self.decider = PkgMatchDecider(pkgs_list)
        self.doc = xapian.Document()

    def test_match(self):
        self.doc.set_data("emacs")
        self.assertTrue(self.decider(self.doc))

    def test_no_match(self):
        self.doc.set_data("gimp")
        self.assertFalse(self.decider(self.doc))


class PkgExpandDeciderTests(unittest.TestCase):

    def setUp(self):
        pkgs_list = ["gimp", "eog", "inkscape"]
        self.decider = PkgExpandDecider(pkgs_list)

    def test_match(self):
        self.assertTrue(self.decider("XPemacs"))

    def test_no_match(self):
        self.assertFalse(self.decider("XTgimp"))


class TagExpandDeciderTests(unittest.TestCase):

    def setUp(self):
        self.decider = TagExpandDecider()

    def test_match(self):
        self.assertTrue(self.decider("XTgimp"))

    def test_no_match(self):
        self.assertFalse(self.decider("gimp"))
