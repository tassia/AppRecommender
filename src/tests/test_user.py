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

import unittest
import xapian

from src.user import User, FilterTag, FilterDescription
from src.config import Config
from src.data import SampleAptXapianIndex


class FilterTagTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):

        tags_filter = "src/tests/test_data/tags_filter"
        self.debtag = "use::searching"

        with open(tags_filter) as valid_tags:
            self.valid_tags = [line.strip() for line in valid_tags]

    def test_call_true(self):
        self.assertTrue(FilterTag(self.valid_tags)("XT" + self.debtag))

    def test_call_false(self):
        self.assertFalse(FilterTag(self.valid_tags)(self.debtag))


class FilterDescriptionTests(unittest.TestCase):
    def test_call_true(self):
        self.assertTrue(FilterDescription()("program"))

    def test_call_false(self):
        self.assertFalse(FilterDescription()("XTprogram"))


class UserTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        cfg = Config()
        self.axi = xapian.Database(cfg.axi)
        packages = ["gimp", "aaphoto", "eog", "emacs", "dia", "ferret",
                    "festival", "file", "inkscape", "xpdf"]
        path = "src/tests/test_data/.sample_axi"
        self.sample_axi = SampleAptXapianIndex(packages, self.axi, path)
        self.user = User({"gimp": 1, "aaphoto": 1, "eog": 1, "emacs": 1})

    def test_hash(self):
        new_user = User(dict())
        self.assertIsNotNone(new_user.id)
        self.assertNotEqual(self.user.id, new_user.id)

    def test_profile_default(self):
        new_user = User(dict())
        desktop = set(["x11", "accessibility", "game", "junior", "office",
                       "interface::x11"])
        self.assertEqual(new_user.demographic_profile, desktop)

    def test_profile_desktop(self):
        self.user.set_demographic_profile(set(["desktop"]))
        desktop = set(["x11", "accessibility", "game", "junior", "office",
                       "interface::x11"])
        self.assertEqual(self.user.demographic_profile, desktop)

    def test_profile_admin(self):
        self.user.set_demographic_profile(set(["admin"]))
        admin = set(["admin", "hardware", "mail", "protocol",
                     "network", "security", "web", "interface::web"])
        self.assertEqual(self.user.demographic_profile, admin)

    def test_profile_devel(self):
        self.user.set_demographic_profile(set(["devel"]))
        devel = set(["devel", "role::devel-lib", "role::shared-lib"])
        self.assertEqual(self.user.demographic_profile, devel)

    def test_profile_art(self):
        self.user.set_demographic_profile(set(["art"]))
        art = set(["field::arts", "sound"])
        self.assertEqual(self.user.demographic_profile, art)

    def test_profile_science(self):
        self.user.set_demographic_profile(set(["science"]))
        science = set(["science", "biology", "field::astronomy",
                       "field::aviation", "field::biology",
                       "field::chemistry", "field::eletronics",
                       "field::finance", "field::geography",
                       "field::geology", "field::linguistics",
                       "field::mathematics", "field::medicine",
                       "field::meteorology", "field::physics",
                       "field::statistics"])
        self.assertEqual(self.user.demographic_profile, science)

    def test_multi_profile(self):
        self.user.set_demographic_profile(set(["devel", "art"]))
        devel_art = set(["devel", "role::devel-lib", "role::shared-lib",
                         "field::arts", "sound"])
        self.assertEqual(self.user.demographic_profile, devel_art)

        self.user.set_demographic_profile(set(["art", "admin", "desktop"]))
        desktop_art_admin = set(["x11", "accessibility", "game", "junior",
                                 "office", "interface::x11", "field::arts",
                                 "sound", "admin", "hardware", "mail",
                                 "protocol", "network", "security", "web",
                                 "interface::web"])
        self.assertEqual(self.user.demographic_profile, desktop_art_admin)

    def test_items(self):
        self.assertEqual(set(self.user.items()),
                         set(["gimp", "aaphoto", "eog", "emacs"]))

    def test_maximal_pkg_profile(self):
        old_pkg_profile = self.user.items()
        aaphoto_deps = ["libc6", "libgomp1", "libjasper1", "libjpeg62",
                        "libpng12-0"]
        libc6_deps = ["libc-bin", "libgcc1"]

        for pkg in aaphoto_deps + libc6_deps:
            self.user.item_score[pkg] = 1

        self.assertEqual(old_pkg_profile, self.user.maximal_pkg_profile())
