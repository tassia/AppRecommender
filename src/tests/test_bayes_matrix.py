#!/usr/bin/env python

import unittest
import numpy as np

from src.bayes_matrix import BayesMatrix


class PkgClassificationTests(unittest.TestCase):
    def test_training(self):
        data_matrix = np.matrix("1 0 1 0 1; 0 1 1 0 1; 1 0 0 1 1; 1 0 1 1 0;\
                                 0 1 1 1 0")
        classifications = np.matrix("1; 2; 0; 1; 2")
        order_of_classifications = [0, 1, 2]

        prob_1 = np.matrix("1 0 0 1 1; 1 0 1 0.5 0.5; 0 1 1 0.5 0.5; 0 0 0 0 0;\
                           0 0 0 0 0").astype(float)
        prob_0 = np.matrix("0 1 1 0 0; 0 1 0 0.5 0.5; 1 0 0 0.5 0.5; 0 0 0 0 0;\
                           0 0 0 0 0").astype(float)

        bayes_matrix = BayesMatrix()
        bayes_matrix.training(data_matrix, classifications,
                              order_of_classifications)

        self.assertTrue(np.allclose(prob_1, bayes_matrix.prob_1))
        self.assertTrue(np.allclose(prob_0, bayes_matrix.prob_0))
