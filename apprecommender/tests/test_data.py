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

import unittest
import xapian

from apprecommender.data import PopconSubmission, axi_search_pkg_tags
from apprecommender.config import Config


class AxiSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        cfg = Config()
        self.axi = xapian.Database(cfg.axi)

    def test_search_pkg_tags(self):
        tags = axi_search_pkg_tags(self.axi, 'apticron')
        print tags
        self.assertEqual(set(tags), set(['XTadmin::package-management',
                                         'XTnetwork::server',
                                         'XTimplemented-in::shell',
                                         'XTrole::program',
                                         'XTsuite::debian', 'XTuse::monitor',
                                         'XTworks-with::mail']))


class PopconSubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.submission_path = "apprecommender/tests/test_data/test_popcon"
        self.submission = PopconSubmission(self.submission_path)

    def test_user_id(self):
        with open(self.submission_path) as popcon_file:
            user_id = popcon_file.readline().split()[2].lstrip("ID:")
        self.assertEqual(self.submission.user_id, user_id)

    def test_load(self):
        with open(self.submission_path) as popcon_file:
            size = len(popcon_file.readlines())
        self.assertEqual(len(self.submission.packages), size - 2)

    def test_str(self):
        output = "\nPopularity-contest submission ID "
        output += "8b44fcdbcf676e711a153d5db099test\n "
        output += "dash: 1\n perl-base: 1\n libusbmuxd1: 1\n "
        output += "libc6-i686: 1\n libc6: 1"
        self.assertEqual(self.submission.__str__(), output)
