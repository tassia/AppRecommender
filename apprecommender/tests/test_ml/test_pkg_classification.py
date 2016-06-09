#!/usr/bin/env python

import apt
import unittest
import xapian

from apprecommender.ml.data import MachineLearningData


class PkgClassificationTests(unittest.TestCase):

    def setUp(self):
        self.ml_data = MachineLearningData()
        self.cache = apt.Cache()

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
        vim_terms = [u'vim', u'compat', u'version', u'unix', u'editor', u'vi',
                     u'new', u'featur', u'ad', u'multi', u'level', u'undo',
                     u'syntax', u'highlight', u'command', u'line', u'histori',
                     u'line', u'help', u'filenam', u'complet', u'block',
                     u'oper', u'fold', u'unicod', u'support', u'packag',
                     u'contain', u'version', u'vim', u'compil', u'standard',
                     u'set', u'featur', u'packag', u'doe', u'provid', u'gui',
                     u'version', u'vim', u'vim', u'packag', u'need']
        vim_terms_result = self.ml_data.get_pkg_terms(self.cache, 'vim')

        print vim_terms_result

        for term in vim_terms:
            self.assertTrue(term in vim_terms_result)

    def test_create_row_table_list(self):
        labels_name = ['devel::editor', 'implemented-in::c', 'complet',
                       'contain', 'syntax', 'unix', 'version']
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
        terms_name = ['vim', 'editor', 'python']

        assert_pkgs_classification = {'vim': [1, 1, 0, 0, 1, 1, 0, 'EX']}

        pkgs_classification = self.ml_data.get_pkgs_table_classification(
            axi, pkgs, self.cache, debtags_name, terms_name)

        self.assertEqual(assert_pkgs_classification, pkgs_classification)
