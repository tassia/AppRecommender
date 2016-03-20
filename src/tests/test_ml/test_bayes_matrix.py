#!/usr/bin/env python

import unittest
import numpy as np

from src.ml.bayes_matrix import BayesMatrix


class PkgClassificationTests(unittest.TestCase):

    def setUp(self):
        self.bayes_matrix = BayesMatrix()

    def test_training(self):
        data_matrix = np.matrix("1 0 1 0 1; 0 1 1 0 1; 1 0 0 1 1; 1 0 1 1 0;\
                                 0 1 1 1 0")
        classifications = np.matrix("1; 2; 0; 1; 2")
        order_of_classifications = [0, 1, 2]

        prob_1 = np.matrix("1 0 0 1 1; 1 0 1 0.5 0.5; 0 1 1 0.5 0.5; 0 0 0 0 0;\
                           0 0 0 0 0").astype(float)
        prob_0 = np.matrix("0 1 1 0 0; 0 1 0 0.5 0.5; 1 0 0 0.5 0.5; 0 0 0 0 0;\
                           0 0 0 0 0").astype(float)

        self.bayes_matrix = BayesMatrix()
        self.bayes_matrix.training(data_matrix, classifications,
                                   order_of_classifications)

        self.assertTrue(np.allclose(prob_1, self.bayes_matrix.prob_1))
        self.assertTrue(np.allclose(prob_0, self.bayes_matrix.prob_0))

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
        self.bayes_matrix.prob_1 = np.matrix(
            "1 0 0 1 1; 1 0 1 0.5 0.5; 0 1 1 0.5 0.5; 0 0 0 0 0;\
             0 0 0 0 0").astype(float)
        self.bayes_matrix.prob_0 = np.matrix(
            "0 1 1 0 0; 0 1 0 0.5 0.5; 1 0 0 0.5 0.5; 0 0 0 0 0;\
             0 0 0 0 0").astype(float)

        attribute_vector = np.matrix("1 0 1 1 0")

        self.assertEqual(
            1, self.bayes_matrix.get_classification(attribute_vector))

    def test_convert_classifications_to_numbers(self):
        classifications = np.array(['M', 'B', 'G'])
        order_of_classifications = ['B', 'M', 'G']

        expected = np.array([[1], [0], [2]])
        actual = self.bayes_matrix.convert_classifications_to_number(
            classifications, order_of_classifications)

        for index, label in enumerate(expected):
            self.assertEqual(label[0], actual[index, 0])
