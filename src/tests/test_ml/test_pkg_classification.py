#!/usr/bin/env python

import apt
import unittest
import xapian

from nltk.corpus import stopwords

from src.ml.data import MachineLearningData

from src.ml.utils import sample_classification


class PkgClassificationTests(unittest.TestCase):

    def setUp(self):
        self.ml_data = MachineLearningData()
        self.cache = apt.Cache()
        self.stop_words = set(stopwords.words('english'))

    def test_sample_classification(self):

        labels = ['EX', 'G', 'M', 'B', 'H']
        threshold = [85, 75, 55, 35, 10]

        self.assertEqual('EX', sample_classification(86, labels, threshold))
        self.assertEqual('G', sample_classification(78, labels, threshold))
        self.assertEqual('M', sample_classification(65, labels, threshold))
        self.assertEqual('B', sample_classification(42, labels, threshold))
        self.assertEqual('H', sample_classification(12, labels, threshold))

    def test_get_pkg_debtags(self):
        vim_debtags = ['devel::editor', 'implemented-in::c',
                       'interface::commandline', 'interface::text-mode',
                       'role::program', 'scope::application',
                       'uitoolkit::ncurses', 'use::editing',
                       'works-with::text', 'works-with::unicode']

        axi_path = "/var/lib/apt-xapian-index/index"
        axi = xapian.Database(axi_path)

        vim_debtags_result = self.ml_data.get_pkg_debtags(axi, 'vim')

        for debtag in vim_debtags:
            self.assertTrue(debtag in vim_debtags_result)

    def test_get_pkg_terms(self):
        vim_terms = [u'vim', u'almost', u'compatible', u'version', u'unix',
                     u'editor', u'vi', u'many', u'new', u'features', u'added',
                     u'multi', u'level', u'undo', u'syntax', u'highlighting',
                     u'command', u'line', u'history', u'line', u'help',
                     u'filename', u'completion', u'block', u'operations',
                     u'folding', u'unicode', u'support', u'etc', u'package',
                     u'contains', u'version', u'vim', u'compiled', u'rather',
                     u'standard', u'set', u'features', u'package', u'provide',
                     u'gui', u'version', u'vim', u'see',
                     u'vim', u'packages', u'need', u'less']

        vim_terms_result = self.ml_data.get_pkg_terms(self.cache, 'vim',
                                                      self.stop_words)

        for debtag in vim_terms:
            self.assertTrue(debtag in vim_terms_result)

    def test_create_row_table_list(self):
        labels_name = ['devel::editor', 'implemented-in::c', 'complet',
                       'Zcontain', 'Zsyntax', 'Zunix', 'Zversion']
        pkg_elements = ['implemented-in::c', 'complet']

        row_list_to_assert = [0, 1, 1, 0, 0, 0, 0]
        row_list = self.ml_data.create_row_table_list(labels_name,
                                                      pkg_elements)

        self.assertEqual(row_list_to_assert, row_list)

    def test_get_pkg_classification(self):
        axi_path = "/var/lib/apt-xapian-index/index"
        axi = xapian.Database(axi_path)
        pkgs = {'vim': 'EX'}
        debtags_name = ['devel::editor', 'implemented-in::c',
                        'devel::interpreter', 'devel::lang:python']
        terms_name = ['contain', 'syntax', 'python']

        assert_pkgs_classification = {'vim': [1, 1, 0, 0, 0, 1, 0, 'EX']}

        pkgs_classification = self.ml_data.get_pkgs_table_classification(
            axi, pkgs, self.cache, self.stop_words, debtags_name, terms_name)

        self.assertEqual(assert_pkgs_classification, pkgs_classification)
