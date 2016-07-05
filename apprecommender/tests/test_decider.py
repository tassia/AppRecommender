import unittest

from apprecommender.decider import PkgInitDecider


class PkgInitDeciderTests(unittest.TestCase):

    def setUp(self):
        self.pkg_init_decider = PkgInitDecider()

    def test_example_pkg_regex(self):
        pkg = 'test-examples'
        self.assertTrue(self.pkg_init_decider.is_pkg_examples(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_examples(pkg))

    def test_dbg_pkg_regex(self):
        pkg = 'test-dbg'
        self.assertTrue(self.pkg_init_decider.is_pkg_dbg(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_dbg(pkg))

    def test_python_pkg_regex(self):
        pkg = 'python-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_python_lib(pkg))

        pkg = 'python3-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_python_lib(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_python_lib(pkg))

    def test_ruby_pkg_regex(self):
        pkg = 'ruby-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_ruby_lib(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_ruby_lib(pkg))

    def test_texlive_pkg_regex(self):
        pkg = 'texlive-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_texlive_lib(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_texlive_lib(pkg))

    def test_pkg_gir_regex(self):
        pkg = 'gir1.2-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_gir_lib(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_gir_lib(pkg))

    def test_pkg_golang_regex(self):
        pkg = 'golang-test'
        self.assertTrue(self.pkg_init_decider.is_pkg_golang_lib(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_golang_lib(pkg))

    def test_pkg_data_regex(self):
        pkg = 'test-data'
        self.assertTrue(self.pkg_init_decider.is_pkg_data(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_data(pkg))

    def test_pkg_dev_regex(self):
        pkg = 'test-dev'
        self.assertTrue(self.pkg_init_decider.is_pkg_dev(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_dev(pkg))

    def test_pkg_utils_regex(self):
        pkg = 'test-utils'
        self.assertTrue(self.pkg_init_decider.is_pkg_utils(pkg))

        pkg = 'test-utils-1.9'
        self.assertTrue(self.pkg_init_decider.is_pkg_utils(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_utils(pkg))

    def test_pkg_common_regex(self):
        pkg = 'test-common'
        self.assertTrue(self.pkg_init_decider.is_pkg_common(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_common(pkg))

    def test_pkg_fonts_regex(self):
        pkg = 'test-fonts'
        self.assertTrue(self.pkg_init_decider.is_pkg_fonts(pkg))

        pkg = 'test-pkg'
        self.assertFalse(self.pkg_init_decider.is_pkg_fonts(pkg))
