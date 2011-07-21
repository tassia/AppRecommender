#!/usr/bin/env python
"""
    dataTests - Data classes test case
"""
__author__ = "Tassia Camoes Araujo <tassia@gmail.com>"
__copyright__ = "Copyright (C) 2011 Tassia Camoes Araujo"
__license__ = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import unittest2
import shutil
import os
import xapian
import sys
sys.path.insert(0,'../')
from data import PopconSubmission, PopconXapianIndex, axi_search_pkg_tags
from config import Config

def suite():
    return unittest2.TestLoader().loadTestsFromTestCase(PopconSubmissionTests)

class AxiSearchTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        cfg = Config()
        self.axi = xapian.Database(cfg.axi)

    def test_search_pkg_tags(self):
        tags = axi_search_pkg_tags(self.axi,'apticron')
        self.assertEqual(set(tags),set(['XTadmin::package-management',
                                        'XTinterface::daemon',
                                        'XTnetwork::server', 'XTrole::program',
                                        'XTsuite::debian', 'XTuse::monitor',
                                        'XTworks-with::mail']))

class PopconSubmissionTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        self.submission_path = "test_data/test_popcon"
        self.submission = PopconSubmission(self.submission_path)

    def test_user_id(self):
        with open(self.submission_path) as popcon_file:
            user_id = popcon_file.readline().split()[2].lstrip("ID:")
        self.assertEqual(self.submission.user_id,user_id)

    def test_load(self):
        with open(self.submission_path) as popcon_file:
            size = len(popcon_file.readlines())
        self.assertEqual(len(self.submission.packages),size-2)

    def test_str(self):
        output = "\nPopularity-contest submission ID 8b44fcdbcf676e711a153d5db099test\n dash: 1\n perl-base: 1\n libusbmuxd1: 1\n libc6-i686: 1\n libc6: 1"
        self.assertEqual(self.submission.__str__(),output)

class PopconXapianIndexTests(unittest2.TestCase):
    def setUp(self):
        self.cfg = Config()
        self.cfg.popcon_index = "test_data/.sample_pxi"
        self.cfg.popcon_dir = "test_data/popcon_dir"
        self.cfg.clusters_dir = "test_data/clusters_dir"
        # build old index for all tests
        shutil.rmtree(self.cfg.popcon_index,1)
        self.assertFalse(os.path.exists(self.cfg.popcon_index))
        # local variable, index will be closed before test
        pxi = PopconXapianIndex(self.cfg)
        self.assertEqual(pxi.get_metadata("old"),"")
        pxi.set_metadata("old","true")

    def test_load(self):
        # load the previously built index
        pxi = PopconXapianIndex(self.cfg)
        self.assertEqual(pxi.get_metadata("old"),"true")

    def test_reindex(self):
        # force reindex with no clustering
        self.cfg.index_mode = "reindex"
        pxi = PopconXapianIndex(self.cfg)
        self.assertEqual(pxi.get_metadata("old"),"")

    def test_clustering(self):
        # force reindex with clustering
        self.cfg.index_mode = "cluster"
        pxi = PopconXapianIndex(self.cfg)
        self.assertEqual(pxi.source_dir,self.cfg.clusters_dir)
        all_submissions = [submissions for (root, dirs, submissions) in
                           os.walk(pxi.source_dir)]
        self.assertEqual(pxi.get_doccount(),
                         sum([len(submissions) for submissions in
                              all_submissions]))

    def test_submissions(self):
        pxi = PopconXapianIndex(self.cfg)
        submissions = pxi.get_submissions(pxi.source_dir)
        all_submissions = [submissions for (root, dirs, submissions) in
                           os.walk(pxi.source_dir)]
        self.assertEqual(len(submissions),
                         sum([len(submissions) for submissions in
                              all_submissions]))

    def test_recluster(self):
        # force reindexing and clustering
        self.cfg.index_mode = "recluster"
        self.cfg.k_medoids = 2
        pxi = PopconXapianIndex(self.cfg)
        self.assertEqual(pxi.source_dir,self.cfg.clusters_dir)
        self.assertEqual(pxi.get_doccount(),2)

if __name__ == '__main__':
        unittest2.main()
