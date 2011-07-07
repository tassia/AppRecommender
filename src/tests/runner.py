#!/usr/bin/env python
"""
    runner - Run the whole set of test cases suites.
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
from user_tests import UserTests, FilterTagTests, FilterDescriptionTests
from recommender_tests import RecommendationResultTests, RecommenderTests
from data_tests import PopconSubmissionTests, PopconXapianIndexTests
from strategy_tests import (PkgMatchDeciderTests, UserMatchDeciderTests,
     PkgExpandDeciderTests, TagExpandDeciderTests, ContentBasedStrategyTests,
     CollaborativeStrategyTests, DemographicStrategyTests,
     KnowledgeBasedStrategyTests, ItemReputationStrategyTests)
from singleton_tests import SingletonTests

def load_tests(test_cases):
    suite = unittest2.TestSuite()
    for test_class in test_cases:
        tests = unittest2.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

test_lists = [[UserTests, FilterTagTests, FilterDescriptionTests],
              [RecommendationResultTests, RecommenderTests],
              [PopconSubmissionTests, PopconXapianIndexTests],
              [PkgMatchDeciderTests, UserMatchDeciderTests,
               PkgExpandDeciderTests, TagExpandDeciderTests,
               ContentBasedStrategyTests, CollaborativeStrategyTests,
               DemographicStrategyTests, KnowledgeBasedStrategyTests,
               ItemReputationStrategyTests],
              [SingletonTests]]

runner = unittest2.TextTestRunner()
for module in test_lists:
    runner.run(load_tests(module))
