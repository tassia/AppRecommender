import unittest
from numpy import array

from src.ml.cross_validation import ConfusionMatrix


class ConfusionMatrixTest(unittest.TestCase):

    def test_confusion_matrix_values(self):
        predicted_results = array([[1], [0], [1], [0]])
        real_results = array([[1], [0], [0], [1]])

        confusion_matrix = ConfusionMatrix(predicted_results, real_results)
        confusion_matrix.run()

        tp, tn, fp, fn = 1, 1, 1, 1
        self.assertEqual(tp, confusion_matrix.tp)
        self.assertEqual(tn, confusion_matrix.tn)
        self.assertEqual(fp, confusion_matrix.fp)
        self.assertEqual(fn, confusion_matrix.fn)
