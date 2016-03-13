#!/usr/bin/env python

import unittest
import xapian

from src.bin.pkg_classification import get_pkgs_table_classification
from src.bin.pkg_classification import get_pkg_debtags
from src.bin.pkg_classification import get_pkg_terms
from src.bin.pkg_classification import sample_classification
from src.bin.pkg_classification import create_row_table_list


class PkgClassificationTests(unittest.TestCase):
    def test_sample_classification(self):
        excelent, great = 85, 75
        medium, bad, horrible = 55, 35, 25

        self.assertEqual('EX', sample_classification(excelent))
        self.assertEqual('G', sample_classification(great))
        self.assertEqual('M', sample_classification(medium))
        self.assertEqual('B', sample_classification(bad))
        self.assertEqual('H', sample_classification(horrible))

    def test_get_pkg_debtags(self):
        vim_debtags = ['devel::editor', 'implemented-in::c',
                       'interface::commandline', 'interface::text-mode',
                       'role::program', 'scope::application',
                       'uitoolkit::ncurses', 'use::editing',
                       'works-with::text', 'works-with::unicode']

        axi_path = "/var/lib/apt-xapian-index/index"
        axi = xapian.Database(axi_path)

        vim_debtags_result = get_pkg_debtags(axi, 'vim')

        for debtag in vim_debtags:
            self.assertTrue(debtag in vim_debtags_result)

    def test_get_pkg_terms(self):
        vim_terms = ['Zalmost', 'Zblock', 'Zcommand', 'Zcompat', 'Zcompil',
                     'Zcomplet', 'Zcontain', 'Zsyntax', 'Zunix', 'Zversion',
                     'Zvi', 'Zvim']

        axi_path = "/var/lib/apt-xapian-index/index"
        axi = xapian.Database(axi_path)

        vim_terms_result = get_pkg_terms(axi, 'vim')

        print vim_terms_result

        for debtag in vim_terms:
            self.assertTrue(debtag in vim_terms_result)

    def test_create_row_table_list(self):
        labels_name = ['devel::editor', 'implemented-in::c', 'complet',
                       'Zcontain', 'Zsyntax', 'Zunix', 'Zversion']
        pkg_elements = ['implemented-in::c', 'complet']

        row_list_to_assert = [0, 1, 1, 0, 0, 0, 0]
        row_list = create_row_table_list(labels_name, pkg_elements)

        self.assertEqual(row_list_to_assert, row_list)

    def test_get_pkg_classification(self):
        axi_path = "/var/lib/apt-xapian-index/index"
        axi = xapian.Database(axi_path)
        pkgs = {'vim': 'EX'}
        debtags_name = ['devel::editor', 'implemented-in::c',
                        'devel::interpreter', 'devel::lang:python']
        terms_name = ['Zcontain', 'Zsyntax', 'Zpython']

        assert_pkgs_classification = {'vim': [1, 1, 0, 0, 1, 1, 0, 'EX']}

        pkgs_classification = (get_pkgs_table_classification(axi, pkgs,
                               debtags_name, terms_name))

        self.assertEqual(assert_pkgs_classification, pkgs_classification)
