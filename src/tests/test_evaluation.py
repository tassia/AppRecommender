#!/usr/bin/env python
"""
    evaluationTests - Evaluation class test case
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
from numpy import array

from src.evaluation import (Accuracy, Precision, Recall, Coverage,
                            Evaluation)
from src.recommender import RecommendationResult
from src.ml.cross_validation import CrossValidationMachineLearning


class MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        repository = ['apple', 'grape', 'pineaple', 'melon',
                      'watermelon', 'orange']
        real = RecommendationResult(dict.fromkeys(['apple', 'grape',
                                                   'pineaple', 'melon'], 1))
        predicted = RecommendationResult(dict.fromkeys(['apple', 'grape',
                                                        'orange'], 1))
        self.evaluation = Evaluation(predicted, real, len(repository))

    def test_class_accuracy(self):
        accuracy = Accuracy().run(self.evaluation)
        self.assertEqual(accuracy, 0.5)

    def test_precision(self):
        precision = Precision().run(self.evaluation)
        self.assertEqual("%.2f" % precision, "0.67")

    def test_recall(self):
        recall = Recall().run(self.evaluation)
        self.assertEqual(recall, 0.5)

    def test_coverage(self):
        evaluations_set = set()
        evaluations_set.add(self.evaluation)
        coverage = Coverage().run(evaluations_set)
        self.assertEqual(coverage, 0.5)

    def test_evaluation(self):
        self.assertEqual(self.evaluation.true_positive, ['apple', 'grape'])
        self.assertEqual(self.evaluation.false_positive, ['orange'])
        self.assertEqual(self.evaluation.false_negative, ['pineaple', 'melon'])


class CrossValidationTests(unittest.TestCase):

    def create_cross_validation_ml(self, partition_proportion, rounds,
                                   metrics_list, labels, thresholds):
        return CrossValidationMachineLearning(partition_proportion, rounds,
                                              metrics_list,
                                              labels, thresholds)

    def test_get_real_results(self):
        cross_validation_ml = self.create_cross_validation_ml(0.1, 1, [], [],
                                                              [])
        test_data = {'test1': [1, 0, 1, 0, 'T'], 'test2': [1, 1, 1, 0, 'F']}

        expected_result = array([['T'], ['F']])
        actual_result = cross_validation_ml.get_real_results(test_data)

        self.assertEquals(expected_result.shape, actual_result.shape)

        for index, label in enumerate(actual_result):
            self.assertEqual(label[0], expected_result[index, 0])
