#!/usr/bin/env python

import unittest
import xapian

from src.bin.pkg_classification import sample_classification
from src.bin.pkg_classification import get_pkg_debtags


class PkgClassificationTests(unittest.TestCase):

    def test_sample_classification(self):
        ex, g, m, b, h = 85, 75, 55, 35, 10

        ex_classification = sample_classification(ex)
        g_classification = sample_classification(g)
        m_classification = sample_classification(m)
        b_classification = sample_classification(b)
        h_classification = sample_classification(h)

        self.assertEqual('EX', ex_classification)
        self.assertEqual('G', g_classification)
        self.assertEqual('M', m_classification)
        self.assertEqual('B', b_classification)
        self.assertEqual('H', h_classification)

    def test_get_pkg_debtags(self):
        pkg_debtags = ['devel::editor', 'implemented-in::c']
        axi = xapian.Database('/var/lib/apt-xapian-index/index')
        pkg_info = get_pkg_debtags(axi, 'vim')

        for debtag in pkg_debtags:
            self.assertIn(debtag, pkg_info)
