#!/usr/bin/env python

import unittest
import numpy as np

from apprecommender.ml.bayes_matrix import BayesMatrix


class PkgClassificationTests(unittest.TestCase):

    def setUp(self):
        self.bayes_matrix = BayesMatrix()

    def test_training(self):
        data_matrix = np.matrix("1 0 1 0 1; 0 1 1 0 1; 1 0 0 1 1; 1 0 1 1 0;\
                                 0 1 1 1 0")
        classifications = np.matrix([[1], [2], [0], [1], [2]])
        order_of_classifications = [0, 1, 2]

        prob = np.matrix("1 0 0 1 1; 1 0 1 0.5 0.5; 0 1 1 0.5 0.5").astype(
            float)

        self.bayes_matrix = BayesMatrix()
        self.bayes_matrix.training(data_matrix, classifications,
                                   order_of_classifications)

        self.assertTrue(np.allclose(prob, self.bayes_matrix.prob))

    def test_get_classification(self):
        self.bayes_matrix = BayesMatrix()
        self.bayes_matrix.data = np.matrix(
            "1 0 1 0 1; 0 1 1 0 1; 1 0 0 1 1; 1 0 1 1 0;\
             0 1 1 1 0").astype(float)
        self.bayes_matrix.labels = np.matrix("0; 1; 2").astype(float)
        self.bayes_matrix.label_probability = (np.matrix(
            "0.2; 0.4; 0.4").astype(float))
        self.bayes_matrix.order_of_classifications = [0, 1, 2]
        self.bayes_matrix.used_order_of_classifications = [0, 1, 2]
        self.bayes_matrix.prob = np.matrix(
            "1 0 0 1 1; 1 0 1 0.5 0.5; 0 1 1 0.5 0.5").astype(float)

        attribute_vector = np.matrix("1 0 1 1 0")

        self.assertEqual(
            1, self.bayes_matrix.get_classification(attribute_vector))

    def test_convert_classifications_to_numbers(self):
        classifications = np.matrix([['M'], ['B'], ['G']])
        order_of_classifications = ['B', 'M', 'G']

        expected = np.array([[1], [0], [2]])
        actual = self.bayes_matrix.convert_classifications_to_number(
            classifications, order_of_classifications)

        for index, label in enumerate(expected):
            self.assertEqual(label[0], actual[index, 0])

    def test_get_used_order_of_classifications(self):
        classifications = np.matrix([['B'], ['G']])
        order_of_classifications = ['B', 'M', 'G']

        expected = ['B', 'G']
        actual = self.bayes_matrix.get_used_order_of_classifications(
            classifications, order_of_classifications)

        self.assertEquals(expected, actual)

        classifications = np.matrix([['M'], ['M'], ['B'], ['G']])
        order_of_classifications = ['B', 'M', 'G']

        expected = ['B', 'M', 'G']
        actual = self.bayes_matrix.get_used_order_of_classifications(
            classifications, order_of_classifications)

        self.assertEquals(expected, actual)

        classifications = np.matrix([['M'], ['G']])
        order_of_classifications = ['B', 'M', 'G']

        expected = ['M', 'G']
        actual = self.bayes_matrix.get_used_order_of_classifications(
            classifications, order_of_classifications)

        classifications = np.matrix([['B']])
        order_of_classifications = ['B', 'M', 'G']

        expected = ['B']
        actual = self.bayes_matrix.get_used_order_of_classifications(
            classifications, order_of_classifications)

        classifications = np.matrix([['B'], ['D'], ['F']])
        order_of_classifications = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

        expected = ['B', 'D', 'F']
        actual = self.bayes_matrix.get_used_order_of_classifications(
            classifications, order_of_classifications)

        self.assertEquals(expected, actual)

        classifications = np.matrix([['B'], ['D'], ['F']])
        order_of_classifications = ['A', 'B', 'C', 'D', 'E', 'F']

        expected = ['B', 'D', 'F']
        actual = self.bayes_matrix.get_used_order_of_classifications(
            classifications, order_of_classifications)

        self.assertEquals(expected, actual)

    def test_dont_change_labels_when_run_training(self):
        data_matrix = np.matrix("1 0 1 0 1; 0 1 1 0 1; 1 0 0 1 1; 1 0 1 1 0")
        classifications = np.matrix([[1], [2], [1], [2]])
        labels = [0, 1, 2]

        self.bayes_matrix = BayesMatrix()
        self.bayes_matrix.training(data_matrix, classifications,
                                   labels)

        expected_labels = [0, 1, 2]
        self.assertEquals(expected_labels, labels)
