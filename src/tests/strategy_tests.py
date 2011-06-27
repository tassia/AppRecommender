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

import unittest2
import xapian
import sys
sys.path.insert(0,'../')
from error import Error
from user import User
from recommender import RecommendationResult
from config import *
#from data import *
from strategy import (PkgMatchDecider, UserMatchDecider, PkgExpandDecider,
                      TagExpandDecider, ContentBasedStrategy,
                      CollaborativeStrategy, DemographicStrategy,
                      KnowledgeBasedStrategy, ItemReputationStrategy)

class PkgMatchDeciderTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        pkgs_list = ["gimp","eog","inkscape"]
        self.decider = PkgMatchDecider(pkgs_list)
        self.doc = xapian.Document()

    def test_match(self):
        self.doc.set_data("emacs")
        self.assertTrue(self.decider(self.doc))

    def test_no_match(self):
        self.doc.set_data("gimp")
        self.assertFalse(self.decider(self.doc))

class UserMatchDeciderTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        user_profile = ["gimp","eog","inkscape", "emacs"]
        self.decider = UserMatchDecider(user_profile)

    def setUp(self):
        self.doc = xapian.Document()

    def test_match(self):
        self.doc.add_term("emacs")
        self.doc.add_term("gimp")
        self.doc.add_term("eog")
        self.assertTrue(self.decider(self.doc))

    def test_no_match(self):
        self.doc.add_term("gimp")
        self.assertFalse(self.decider(self.doc))

class PkgExpandDeciderTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        self.decider = PkgExpandDecider()

    def test_match(self):
        self.assertTrue(self.decider("XPgimp"))

    def test_no_match(self):
        self.assertFalse(self.decider("XTgimp"))

class TagExpandDeciderTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        self.decider = TagExpandDecider()

    def test_match(self):
        self.assertTrue(self.decider("XTgimp"))

    def test_no_match(self):
        self.assertFalse(self.decider("gimp"))

class ContentBasedStrategyTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        
        pass

class CollaborativeStrategyTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        pass

class DemographicStrategyTests(unittest2.TestCase):
    def test_call(self):
        self.assertRaises(Error,lambda: DemographicStrategy())

class KnowledgeBasedStrategyTests(unittest2.TestCase):
    def test_call(self):
        self.assertRaises(Error,lambda: KnowledgeBasedStrategy())

class ItemReputationStrategyTests(unittest2.TestCase):
    def test_call(self):
        self.assertRaises(Error,lambda: ItemReputationStrategy())

if __name__ == '__main__':
        unittest2.main()
