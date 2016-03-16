import unittest
from numpy import array

from src.ml.utils import create_binary_matrix


class MLUtilsTest(unittest.TestCase):

    def test_create_binary_matrix(self):
        test_matrix = array([[2], [3], [2], [4]])
        classification = 2
        default_value = 0

        expected_result = array([[2], [0], [2], [0]])
        actual_result = create_binary_matrix(test_matrix, classification,
                                             default_value)

        self.assertEquals(expected_result.shape, actual_result.shape)

        num_data = len(actual_result)

        for i in range(num_data):
            self.assertEqual(expected_result[i][0], actual_result[i][0])
