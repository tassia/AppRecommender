import unittest
from numpy import array

from src.ml.cross_validation import (ConfusionMatrix,
                                     CrossValidationMachineLearning)


class ConfusionMatrixTest(unittest.TestCase):

    def test_confusion_matrix_values(self):
        predicted_results = array([[1], [0], [1], [0]])
        real_results = array([[1], [0], [0], [1]])

        confusion_matrix = ConfusionMatrix(predicted_results, real_results)
        confusion_matrix.run()

        tp, tn, fp, fn = 1, 1, 1, 1
        self.assertEqual(tp, confusion_matrix.true_positive)
        self.assertEqual(tn, confusion_matrix.true_negative)
        self.assertEqual(fp, confusion_matrix.false_positive)
        self.assertEqual(fn, confusion_matrix.false_negative)


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
