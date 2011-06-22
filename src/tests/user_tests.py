#!/usr/bin/env python
"""
    userTests - User class test case
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

import operator
import math
import unittest2
import xapian
import sys
sys.path.insert(0,'../')
from user import *
from config import *
from data import *
from pxi import *

def suite():
    return unittest2.TestLoader().loadTestsFromTestCase(UserTests)

class UserTests(unittest2.TestCase):
    @classmethod
    def setUpClass(self):
        cfg = Config()
        self.axi = xapian.Database(cfg.axi)
        self.user = User({"gimp":1,"aaphoto":1,"eog":1,"emacs":1})
        self.pxi = PkgXapianIndex()

    def test_hash(self):
        new_user = User(dict())
        self.assertIsNotNone(new_user.id)
        self.assertNotEqual(self.user.id, new_user.id)

    def test_profile_default(self):
        new_user = User(dict())
        desktop = set(["x11", "accessibility", "game", "junior", "office",
                       "interface::x11"])
        self.assertEqual(new_user.demographic_profile,desktop)

    def test_profile_desktop(self):
        self.user.set_demographic_profile(set(["desktop"]))
        desktop = set(["x11", "accessibility", "game", "junior", "office",
                       "interface::x11"])
        self.assertEqual(self.user.demographic_profile,desktop)

    def test_profile_admin(self):
        self.user.set_demographic_profile(set(["admin"]))
        admin = set(["admin", "hardware", "mail", "protocol",
                     "network", "security", "web", "interface::web"])
        self.assertEqual(self.user.demographic_profile,admin)

    def test_profile_devel(self):
        self.user.set_demographic_profile(set(["devel"]))
        devel = set(["devel", "role::devel-lib", "role::shared-lib"])
        self.assertEqual(self.user.demographic_profile,devel)

    def test_profile_art(self):
        self.user.set_demographic_profile(set(["art"]))
        art = set(["field::arts", "sound"])
        self.assertEqual(self.user.demographic_profile,art)

    def test_profile_science(self):
        self.user.set_demographic_profile(set(["science"]))
        science = set(["science", "biology", "field::astronomy",
                       "field::aviation",  "field::biology",
                       "field::chemistry", "field::eletronics",
                       "field::finance", "field::geography",
                       "field::geology", "field::linguistics",
                       "field::mathematics", "field::medicine",
                       "field::meteorology", "field::physics",
                       "field::statistics"])
        self.assertEqual(self.user.demographic_profile,science)

    def test_multi_profile(self):
        self.user.set_demographic_profile(set(["devel","art"]))
        devel_art = set(["devel", "role::devel-lib", "role::shared-lib",
                         "field::arts", "sound"])
        self.assertEqual(self.user.demographic_profile,devel_art)

        self.user.set_demographic_profile(set(["art","admin","desktop"]))
        desktop_art_admin = set(["x11", "accessibility", "game", "junior",
                                 "office", "interface::x11", "field::arts",
                                 "sound", "admin", "hardware", "mail",
                                 "protocol", "network", "security", "web",
                                 "interface::web"])
        self.assertEqual(self.user.demographic_profile,desktop_art_admin)

    def test_items(self):
        self.assertEqual(self.user.items(),set(["gimp","aaphoto","eog","emacs"]))

    def test_axi_tag_profile(self):
        enquire = xapian.Enquire(self.pxi)
        relevant_dict = {}
        non_relevant_dict = {}
        package_terms = ["XP"+package for package in self.user.items()]
        enquire.set_query(xapian.Query(xapian.Query.OP_OR,package_terms))
        mset = enquire.get_mset(0, self.pxi.get_doccount(), None, None)
        tag_terms = set()
        for m in mset:
            tag_terms = [x.term for x in m.document.termlist()
                         if x.term.startswith("XT")]
            for tag in tag_terms:
                if tag in relevant_dict:
                    relevant_dict[tag] = relevant_dict[tag]+1
                else:
                    relevant_dict[tag] = 1
        rank = {}
        for tag,count in relevant_dict.items():
            non_relevant_dict[tag] = self.pxi.get_termfreq(tag)-count
            if non_relevant_dict[tag]>0:
                rank[tag] = relevant_dict[tag]/float(non_relevant_dict[tag])
        #print "relevant",relevant_dict
        #print "non_relevant",non_relevant_dict
        #print sorted(rank.items(), key=operator.itemgetter(1))
        #[FIXME] get ths value based on real ranking
        self.assertEqual(set(self.user.axi_tag_profile(self.pxi,4)),
                         set(["XTuse::editing", "XTworks-with::image",
                              "XTworks-with-format::png",
                              "XTworks-with-format::jpg"]))


if __name__ == '__main__':
        unittest2.main()
