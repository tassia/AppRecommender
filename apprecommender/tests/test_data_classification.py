#!/usr/bin/env python

import unittest

from apprecommender.data_classification import linear_percent_function


class DataClassificationTests(unittest.TestCase):
    def test_linear_percent_function(self):
        modify, access, time_now = 100, 175, 200

        percent = linear_percent_function(modify, access, time_now)

        self.assertEqual(0.75, percent)
