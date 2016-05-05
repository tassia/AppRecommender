import unittest
from collections import OrderedDict
from numpy import array, matrix

from src.ml.cross_validation import (ConfusionMatrix,
                                     CrossValidationBVA,
                                     Evaluation)
from src.evaluation import (SimpleAccuracy, Precision, Recall, FPR,
                            F_score, MCC, Accuracy)


class ConfusionMatrixTest(unittest.TestCase):

    def test_confusion_matrix_values(self):
        predicted_results = array([[1], [0], [1], [0]])
        real_results = array([[1], [0], [0], [1]])

        confusion_matrix = ConfusionMatrix(predicted_results, real_results)
        confusion_matrix.run()

        tp, tn, fp, fn = 1, 1, 1, 1
        self.assertEqual(tp, confusion_matrix.true_positive_len)
        self.assertEqual(tn, confusion_matrix.true_negative_len)
        self.assertEqual(fp, confusion_matrix.false_positive_len)
        self.assertEqual(fn, confusion_matrix.false_negative_len)

        predicted_results = array([[1], [1], [1], [0]])
        real_results = array([[1], [1], [0], [1]])

        confusion_matrix = ConfusionMatrix(predicted_results, real_results)
        confusion_matrix.run()

        tp, tn, fp, fn = 2, 0, 1, 1
        self.assertEqual(tp, confusion_matrix.true_positive_len)
        self.assertEqual(tn, confusion_matrix.true_negative_len)
        self.assertEqual(fp, confusion_matrix.false_positive_len)
        self.assertEqual(fn, confusion_matrix.false_negative_len)


class EvaluationTest(unittest.TestCase):

    def create_evaluation(self, predicted_values, real_values, labels):
        return Evaluation(predicted_values, real_values, labels)

    def test_evaluation_simple_accuracy(self):
        labels = [1, 2, 3]
        predicted_values = array([[1], [2], [3], [2], [1]])
        real_values = array([[1], [2], [2], [1], [3]])
        metric = SimpleAccuracy()

        evaluation = self.create_evaluation(predicted_values, real_values,
                                            labels)
        results = evaluation.run(metric)
        expected_label_1 = 0.6
        expected_label_2 = 0.6
        expected_label_3 = 0.6

        self.assertEquals(expected_label_1, results[1])
        self.assertEquals(expected_label_2, results[2])
        self.assertEquals(expected_label_3, results[3])


class CrossValidationTests(unittest.TestCase):

    def create_cross_validation_ml(self, pkg_data, partition_proportion,
                                   rounds, metrics_list, labels):
        return CrossValidationBVA(
            pkg_data, partition_proportion, rounds, metrics_list,
            labels)

    def compare_column_matrix(self, expected_matrix, actual_matrix):
        self.assertEquals(expected_matrix.shape, actual_matrix.shape)
        num_itens = actual_matrix.shape[0]

        for i in range(num_itens):
            self.assertEqual(expected_matrix[i, 0], actual_matrix[i, 0])

    def test_get_real_results(self):
        cross_validation_ml = self.create_cross_validation_ml(
            None, 0.1, 1, [], [])
        test_data = {'test1': [1, 0, 1, 0, 'T'], 'test2': [1, 1, 1, 0, 'F']}

        expected_result = array([['T'], ['F']])
        actual_result = cross_validation_ml.get_real_results(test_data)

        self.compare_column_matrix(expected_result, actual_result)

    def test_cross_validation_process(self):
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

        partition_proportion = 0.7
        rounds = 1
        metrics_list = [SimpleAccuracy()]
        labels = ['B', 'M', 'G']

        cross_validation_ml = CrossValidationBVA(
            data_matrix, partition_proportion, rounds, metrics_list,
            labels)

        self.assertEquals(len(data_matrix),
                          len(cross_validation_ml.get_user_score(None)))

        expected_num_B = 3  # noqa
        expected_num_G = 4  # noqa
        expected_num_M = 3  # noqa

        for label in labels:
            self.assertEqual(eval('expected_num_{0}'.format(label)),
                             len(cross_validation_ml.label_groups[label]))

        expected_num_data = 10
        self.assertEqual(expected_num_data, len(cross_validation_ml.pkg_data))

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
        histogram = array([[3], [3], [4]])

        actual_labels_number = bayes_model.labels
        actual_classifications_number = bayes_model.classifications
        actual_histogram = bayes_model.histogram

        self.assertEquals(data.shape, bayes_model.data.shape)
        self.compare_column_matrix(labels_number, actual_labels_number)
        self.compare_column_matrix(classifications_numbers,
                                   actual_classifications_number)
        self.compare_column_matrix(histogram, actual_histogram)

        predictions = cross_validation_ml.get_predicted_results(bayes_model,
                                                                data_matrix)
        expected_shape = (10, 1)

        self.assertEquals(expected_shape, predictions.shape)

        for i in range(len(predictions)):
            self.assertIn(predictions[i, 0], labels)

        real_results = cross_validation_ml.get_real_results(data_matrix)

        cross_validation_ml.run_metrics(predictions, real_results)


class MetricsTest(unittest.TestCase):

    def test_simple_accuracy(self):
        predicted_results = array([[1], [1], [0], [0]])
        actual_results = array([[1], [1], [0], [1]])
        labels = [0, 1]
        metric = SimpleAccuracy()

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0.75
        expected_0 = 0.75

        self.assertEquals(expected_1, results[1])
        self.assertEquals(expected_0, results[0])

    def test_precision(self):
        predicted_results = array([[1], [1], [0], [0]])
        actual_results = array([[1], [1], [0], [1]])
        labels = [0, 1]
        metric = Precision()

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 1
        expected_0 = 0.5

        self.assertEquals(expected_1, results[1])
        self.assertEquals(expected_0, results[0])

        predicted_results = array([[0], [0], [0], [0]])

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0
        expected_0 = 0.25

        self.assertEquals(expected_1, results[1])
        self.assertEquals(expected_0, results[0])

    def test_recall(self):
        predicted_results = array([[1], [1], [0], [0], [1]])
        actual_results = array([[1], [1], [0], [1], [1]])
        labels = [0, 1]
        metric = Recall()

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0.75
        expected_0 = 1

        self.assertEquals(expected_1, results[1])
        self.assertEquals(expected_0, results[0])

        predicted_results = array([[0], [0], [1], [0], [0]])
        actual_results = array([[1], [1], [0], [1], [1]])

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0
        expected_0 = 0

        self.assertEquals(expected_1, results[1])
        self.assertEquals(expected_0, results[0])

    def test_fpr(self):
        predicted_results = array([[1], [1], [0], [1], [0]])
        actual_results = array([[0], [0], [0], [1], [0]])
        labels = [0, 1]
        metric = FPR()

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0.5
        expected_0 = 0

        self.assertEquals(expected_1, results[1])
        self.assertEquals(expected_0, results[0])

    def test_f1_score(self):
        predicted_results = array([[1], [1], [0], [1], [0], [1]])
        actual_results = array([[1], [1], [1], [0], [1], [1]])
        labels = [0, 1]
        metric = F_score(1)

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0.6666666666666666
        expected_0 = 0

        self.assertAlmostEqual(expected_1, results[1])
        self.assertEqual(expected_0, results[0])

    def test_f0_5_score(self):
        predicted_results = array([[1], [1], [0], [1], [0], [1]])
        actual_results = array([[1], [1], [1], [0], [1], [1]])
        labels = [0, 1]
        metric = F_score(0.5)

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0.71428571
        expected_0 = 0

        self.assertAlmostEqual(expected_1, results[1])
        self.assertEqual(expected_0, results[0])

    def test_f2_score(self):
        predicted_results = array([[1], [1], [0], [1], [0], [1]])
        actual_results = array([[1], [1], [1], [0], [1], [1]])
        labels = [0, 1]
        metric = F_score(2)

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1 = 0.625
        expected_0 = 0

        self.assertAlmostEqual(expected_1, results[1])
        self.assertEqual(expected_0, results[0])

    def test_mcc_score(self):
        predicted_results = array([[1], [1], [0], [1], [0], [1]])
        actual_results = array([[1], [1], [1], [0], [0], [1]])
        labels = [0, 1]
        metric = MCC()

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1, expected_0 = 0.25, 0.25

        self.assertAlmostEqual(expected_1, results[1])
        self.assertEqual(expected_0, results[0])

    def test_accuracy(self):
        predicted_results = array([[1], [1], [0], [1], [0], [1]])
        actual_results = array([[1], [1], [1], [0], [0], [1]])
        labels = [0, 1]
        metric = Accuracy()

        evaluation = Evaluation(predicted_results, actual_results, labels)
        results = evaluation.run(metric)

        expected_1, expected_0 = 0.625, 0.625

        self.assertAlmostEqual(expected_1, results[1])
        self.assertEqual(expected_0, results[0])
