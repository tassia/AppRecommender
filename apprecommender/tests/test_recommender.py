#!/usr/bin/env python
"""
    recommenderTests - Recommender class test case
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

from apprecommender.recommender import RecommendationResult, Recommender
from apprecommender.user import User
from apprecommender.config import Config
from apprecommender.strategy import (ContentBased, MachineLearningBVA,
                                     MachineLearningBOW)


class RecommendationResultTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.result = RecommendationResult({"gimp": 1.5, "inkscape": 3.0,
                                            "eog": 1})

    def test_str(self):
        rec = '\n1: inkscape             \t vector-based drawing program\n'
        rec += '2: gimp                 \t The GNU Image Manipulation Program\n'  # noqa
        rec += '3: eog                  \t Eye of GNOME graphics viewer program\n'  # noqa
        self.assertEqual(self.result.__str__(), rec)

    def test_get_prediction(self):
        prediction = [("inkscape", 3.0), ("gimp", 1.5), ("eog", 1)]
        self.assertEqual(self.result.get_prediction(), prediction)


class RecommenderTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        cfg = Config()
        cfg.popcon_index = "test_data/.sample_pxi"
        cfg.popcon_dir = "test_data/popcon_dir"
        cfg.clusters_dir = "test_data/clusters_dir"
        cfg.popcon = 0
        self.rec = Recommender()

    def test_set_strategy(self):
        self.rec.set_strategy("cb")
        self.assertIsInstance(self.rec.strategy, ContentBased)
        self.assertEqual(self.rec.strategy.content, "mix")
        self.rec.set_strategy("cbt")
        self.assertIsInstance(self.rec.strategy, ContentBased)
        self.assertEqual(self.rec.strategy.content, "tag")
        self.rec.set_strategy("cbd")
        self.assertIsInstance(self.rec.strategy, ContentBased)
        self.assertEqual(self.rec.strategy.content, "desc")
        self.rec.set_strategy("cbtm")
        self.assertIsInstance(self.rec.strategy, ContentBased)
        self.assertEqual(self.rec.strategy.content, "time")
        self.rec.set_strategy("mlbva")
        self.assertIsInstance(self.rec.strategy, MachineLearningBVA)
        self.assertEqual(self.rec.strategy.content, "mlbva_mix")
        self.rec.set_strategy("mlbow")
        self.assertIsInstance(self.rec.strategy, MachineLearningBOW)
        self.assertEqual(self.rec.strategy.content, "mlbow_mix")
        self.rec.set_strategy("mlbva_eset")
        self.assertIsInstance(self.rec.strategy, MachineLearningBVA)
        self.assertEqual(self.rec.strategy.content, "mlbva_mix_eset")
        self.rec.set_strategy("mlbow_eset")
        self.assertIsInstance(self.rec.strategy, MachineLearningBOW)
        self.assertEqual(self.rec.strategy.content, "mlbow_mix_eset")

    def test_get_recommendation(self):
        user = User({"inkscape": 1, "gimp": 1, "eog": 1, "vim": 1})
        result = self.rec.get_recommendation(user)
        self.assertIsInstance(result, RecommendationResult)
        self.assertGreater(len(result.item_score), 0)
