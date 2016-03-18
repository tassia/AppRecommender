import unittest
from collections import OrderedDict
from numpy import array, matrix
from mock import patch

from src.ml.cross_validation import (ConfusionMatrix,
                                     CrossValidationMachineLearning)
from src.evaluation import SimpleAccuracy


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

    def compare_column_matrix(self, expected_matrix, actual_matrix):
        self.assertEquals(expected_matrix.shape, actual_matrix.shape)
        num_itens = actual_matrix.shape[0]

        for i in range(num_itens):
            self.assertEqual(expected_matrix[i, 0], actual_matrix[i, 0])

    @patch('src.ml.data.MachineLearningData.create_data')
    def test_cross_validation_process(self, mock_create_data):
        data_matrix = (('test1', [1, 0, 1, 0, 1, 1, 1, 1, 'G']),
                       ('test2', [0, 1, 0, 1, 1, 1, 1, 0, 'M']),
                       ('test3', [1, 0, 1, 0, 1, 0, 0, 1, 'B']),
                       ('test4', [0, 0, 0, 0, 1, 1, 1, 1, 'M']),
                       ('test5', [1, 1, 1, 1, 0, 0, 0, 1, 'G']),
                       ('test6', [1, 1, 0, 0, 1, 1, 0, 0, 'M']),
                       ('test7', [0, 0, 1, 0, 1, 0, 1, 1, 'B']),
                       ('test8', [1, 1, 1, 0, 0, 0, 1, 0, 'G']),
                       ('test9', [0, 1, 1, 0, 0, 1, 1, 1, 'B']),
                       ('test10', [1, 1, 1, 0, 1, 0, 0, 1, 'G']))
        data_matrix = OrderedDict(data_matrix)
        mock_create_data.return_value = data_matrix

        partition_proportion = 0.7
        rounds = 1
        metrics_list = [SimpleAccuracy()]
        labels = ['B', 'M', 'G']
        thresholds = [30, 60, 80]

        cross_validation_ml = CrossValidationMachineLearning(
            partition_proportion, rounds, metrics_list, labels, thresholds)

        self.assertEquals(len(data_matrix),
                          len(cross_validation_ml.get_user_score(None)))

        bayes_model = cross_validation_ml.get_model(data_matrix)
        data = array([[1, 0, 1, 0, 1, 1, 1, 1],
                      [0, 1, 0, 1, 1, 1, 1, 0],
                      [1, 0, 1, 0, 1, 0, 0, 1],
                      [0, 0, 0, 0, 1, 1, 1, 1],
                      [1, 1, 1, 1, 0, 0, 0, 1],
                      [1, 1, 0, 0, 1, 1, 0, 0],
                      [0, 0, 1, 0, 1, 0, 1, 1],
                      [1, 1, 1, 0, 0, 0, 1, 0],
                      [0, 1, 1, 0, 0, 1, 1, 1],
                      [1, 1, 1, 0, 1, 0, 0, 1]])

        labels_number = matrix([[0], [1], [2]])
        classifications_numbers = matrix([[2], [1], [0], [1], [2], [1], [0],
                                          [2], [0], [2]])

        actual_labels_number = bayes_model.labels
        actual_classifications_number = bayes_model.classifications
        print actual_classifications_number

        self.assertEquals(data.shape, bayes_model.data.shape)
        self.compare_column_matrix(labels_number, actual_labels_number)
        self.compare_column_matrix(classifications_numbers,
                                   actual_classifications_number)
