import unittest

from apprecommender.decider import PkgInitDecider


class PkgInitDeciderTests(unittest.TestCase):

    def setUp(self):
        self.pkg_init_decider = PkgInitDecider()

    def test_python_pkg_regex(self):
        pkg = 'python-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'python3-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_ruby_pkg_regex(self):
        pkg = 'ruby-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_texlive_pkg_regex(self):
        pkg = 'texlive-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_gir_regex(self):
        pkg = 'gir1.2-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_golang_regex(self):
        pkg = 'golang-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_data_regex(self):
        pkg = 'test-data'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_dev_regex(self):
        pkg = 'test-dev'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_utils_regex(self):
        pkg = 'test-utils'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-utils-1.9'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_common_regex(self):
        pkg = 'test-common'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_fonts_regex(self):
        pkg = 'test-fonts'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_png_regex(self):
        pkg = 'test-png'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_core_regex(self):
        pkg = 'test-core'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

    def test_pkg_default_regex(self):
        pkg = 'test-default'
        self.assertTrue(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_a_prefix_or_suffix(pkg))
