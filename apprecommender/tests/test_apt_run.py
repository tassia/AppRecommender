#!/usr/bin/env python

import commands
import os
import shutil
import unittest

from mock import patch

from apprecommender.main.apt_run import AptRun


class AptRunTests(unittest.TestCase):

    TEST_FOLDER = 'apprecommender/tests/.apt_run'

    def setUp(self):
        if os.path.exists(AptRunTests.TEST_FOLDER):
            shutil.rmtree(AptRunTests.TEST_FOLDER)

    def test_enable_apt_run(self):
        apt_run = AptRun()
        apt_run.set_folder(AptRunTests.TEST_FOLDER)

        apt_run.enable()
        result = apt_run.is_enable()

        self.assertTrue(result)

    def test_dont_enable_apt_run_if_already_enabled(self):
        apt_run = AptRun()
        apt_run.set_folder(AptRunTests.TEST_FOLDER)

        apt_run.enable()
        result = apt_run.enable()

        self.assertFalse(result)

    def test_disable_apt_run(self):
        apt_run = AptRun()
        apt_run.set_folder(AptRunTests.TEST_FOLDER)

        os.makedirs(AptRunTests.TEST_FOLDER)
        apt_run.disable()
        result = apt_run.is_enable()

        self.assertFalse(result)

    def test_dont_disable_apt_run_if_already_disabled(self):
        apt_run = AptRun()
        apt_run.set_folder(AptRunTests.TEST_FOLDER)

        result = apt_run.disable()

        self.assertFalse(result)

    def test_pre_install_pkgs(self):
        apt_run = AptRun()
        apt_run.set_folder(AptRunTests.TEST_FOLDER)
        apt_run.enable()
        apt_run.pre_install_pkgs()

        assert_pkgs = commands.getoutput("apt-mark showmanual").splitlines()
        assert_pkgs = sorted(assert_pkgs)

        pkgs = []
        with open(apt_run.installed_pkgs_file, 'r') as text:
            pkgs = [line.strip() for line in text]
            pkgs = sorted(pkgs)

        self.assertListEqual(assert_pkgs, pkgs)

    @patch('apprecommender.main.apt_run.AptRun.get_user_pkgs')
    def test_post_invoke(self, mock_user_pkgs):
        mock_user_pkgs.return_value = ['vim', 'gedit']

        apt_run = AptRun()
        apt_run.set_folder(AptRunTests.TEST_FOLDER)
        apt_run.enable()

        with open(apt_run.installed_pkgs_file, 'w') as text:
            text.write('gedit')

        installed_pkgs = apt_run.post_invoke()

        self.assertEqual(['vim'], installed_pkgs)
