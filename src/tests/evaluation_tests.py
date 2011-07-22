#!/usr/bin/env python
"""
    singletonTests - Singleton class test case
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

import xapian
import unittest2
import sys
sys.path.insert(0,'../')
from evaluation import (Accuracy, Precision, Recall, F1, Coverage,
                        Evaluation, CrossValidation)
from recommender import RecommendationResult
from config import Config
from recommender import Recommender
from user import User
from data import SampleAptXapianIndex

class MetricsTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        repository = ['apple','grape','pineaple','melon','watermelon','orange']
        real = RecommendationResult(dict.fromkeys(['apple','grape','pineaple','melon'],1))
        predicted = RecommendationResult(dict.fromkeys(['apple','grape','orange'],1))
        self.evaluation = Evaluation(predicted,real,len(repository))

    def test_class_accuracy(self):
        accuracy = Accuracy().run(self.evaluation)
        self.assertEqual(accuracy,0.5)

    def test_precision(self):
        precision = Precision().run(self.evaluation)
        self.assertEqual("%.2f" % precision,"0.67")

    def test_recall(self):
        recall = Recall().run(self.evaluation)
        self.assertEqual(recall,0.5)

    def test_f1(self):
        f1 = F1().run(self.evaluation)
        self.assertEqual("%.2f" % f1,"0.57")

    def test_coverage(self):
        evaluations_set = set()
        evaluations_set.add(self.evaluation)
        coverage = Coverage().run(evaluations_set)
        self.assertEqual(coverage,0.5)

    def test_evaluation(self):
        self.assertEqual(self.evaluation.true_positive, ['apple','grape'])
        self.assertEqual(self.evaluation.false_positive, ['orange'])
        self.assertEqual(self.evaluation.false_negative, ['pineaple','melon'])

    def test_cross_validation(self):
        cfg = Config()
        axi = xapian.Database(cfg.axi)
        packages = ["gimp","aaphoto","eog","emacs","dia","ferret",
                    "festival","file","inkscape","xpdf"]
        path = "test_data/.sample_axi"
        sample_axi = SampleAptXapianIndex(packages,axi,path)
        rec = Recommender(cfg)
        rec.items_repository = sample_axi
        user = User({"gimp":1,"aaphoto":1,"eog":1,"emacs":1})

        metrics = []
        metrics.append(Precision())
        metrics.append(Recall())
        metrics.append(F1())

        validation = CrossValidation(0.3,5,rec,metrics,0.5)
        validation.run(user)
        print validation

if __name__ == '__main__':
        unittest2.main()
