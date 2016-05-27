#!/usr/bin/env python

import unittest

from apprecommender.initialize import Initialize


class InitializeTests(unittest.TestCase):

    def test_get_tags(self):
        initialize = Initialize()
        tags = initialize.get_tags()

        self.assertTrue(len(tags) > 0)

        combined_tags = ''.join(tags)
        for tag in Initialize.EXCLUDED_TAGS:
            self.assertTrue(tag not in combined_tags)

    def test_get_axipkgs(self):
        initialize = Initialize()
        pkgs = initialize.get_axipkgs()

        self.assertTrue(len(pkgs) > 0)
