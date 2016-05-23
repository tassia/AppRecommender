#!/usr/bin/env python

import unittest
import numpy as np

from apprecommender.ml.pkg_time import PkgTime


class PkgTimeTests(unittest.TestCase):

    def test_access_time_greater_than_modify_time(self):
        pkg_time = PkgTime()
        pkgs_time = pkg_time.create_pkg_data()

        for _, times in pkgs_time.iteritems():
            modify, access = times
            self.assertTrue(access >= modify)
