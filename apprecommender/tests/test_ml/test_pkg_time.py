#!/usr/bin/env python

import unittest
from mock import patch

from apprecommender.ml.pkg_time import PkgTime


class PkgTimeTests(unittest.TestCase):

    def setUp(self):
        self.pkg_time = PkgTime()

    @patch('commands.getoutput')
    @patch('apprecommender.ml.pkg_time.get_time_from_package')
    def test_invalid_paths_get_best_time(self, mock_time, mock_command):
        mock_time.return_value = [10, 10]

        mock_command.return_value = '/usr/lib/a-b-c/\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

        mock_command.return_value = '/usr/lib/a-b-c-d/\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

        mock_command.return_value = '/usr/lib/mime/packages/test\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

        mock_command.return_value = '/etc/init.d/test\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

        mock_command.return_value = '/media/files/test\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

    @patch('commands.getoutput')
    @patch('apprecommender.ml.pkg_time.get_time_from_package')
    def test_valid_paths_get_best_time(self, mock_time, mock_command):
        mock_time.return_value = [10, 10]
        mock_command.return_value = '/usr/lib/a-b/\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 10)
        self.assertEqual(modify, 10)

        mock_time.return_value = [20, 20]
        mock_command.return_value = '/usr/bin/test\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 20)
        self.assertEqual(modify, 20)

        mock_time.return_value = [30, 30]
        mock_command.return_value = '/usr/game/test\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 30)
        self.assertEqual(modify, 30)

        mock_time.return_value = [40, 40]
        mock_command.return_value = '/usr/lib/test/test\n'
        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 40)
        self.assertEqual(modify, 40)

    @patch('commands.getoutput')
    @patch('apprecommender.ml.pkg_time.get_time_from_package')
    def test_invalid_files_get_best_time(self, mock_time, mock_command):
        mock_time.return_value = [10, 10]
        mock_command.return_value = '/usr/bin/test.desktop\n'

        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

        mock_time.return_value = [10, 10]
        mock_command.return_value = '/usr/games/test.conf\n'

        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

        mock_time.return_value = [10, 10]
        mock_command.return_value = '/usr/lib/python/test.egg-info\n'

        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)

        mock_time.return_value = [10, 10]
        mock_command.return_value = '/usr/lib/test/test.txt\n'

        access, modify = self.pkg_time.get_best_time('test')

        self.assertEqual(access, 0)
        self.assertEqual(modify, 0)
