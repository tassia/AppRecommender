#!/usr/bin/env python

import commands
import lzma
import os
import shutil
import unittest

from mock import patch

from apprecommender.collaborative_data import (CollaborativeData,
                                               PopconSubmission)


COLLABORATIVE_DATA_DIR = 'apprecommender/tests/test_data/' \
                         '.popcon_clusters_tests/'
INRELEASE_FILE = COLLABORATIVE_DATA_DIR + 'InRelease'
CLUSTERS_FILE = COLLABORATIVE_DATA_DIR + 'clusters.txt'
CLUSTERS_FILE_XZ = COLLABORATIVE_DATA_DIR + 'clusters.xz'
PKGS_CLUSTERS_FILE = COLLABORATIVE_DATA_DIR + 'pkgs_clusters.txt'
PKGS_CLUSTERS_FILE_XZ = COLLABORATIVE_DATA_DIR + 'pkgs_clusters.xz'


class CollaborativeDataTests(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(COLLABORATIVE_DATA_DIR):
            shutil.rmtree(COLLABORATIVE_DATA_DIR)

    def compress_file(self, source, destiny):
        if os.path.exists(destiny):
            os.remove(destiny)

        with open(source, 'rb') as input_file:
            with open(destiny, 'wb') as output_file:
                data = lzma.compress(bytes(input_file.read()))
                output_file.write(data)

        os.remove(source)

    def create_collaborative_data_dir(self):
        if os.path.exists(COLLABORATIVE_DATA_DIR):
            shutil.rmtree(COLLABORATIVE_DATA_DIR)
        os.mkdir(COLLABORATIVE_DATA_DIR)

        clusters = [[1.0, 0.0, 1.0, 0.0, 1.0],
                    [0.0, 1.0, 0.0, 1.0, 1.0],
                    [1.0, 0.0, 0.0, 1.0, 0.0]]
        with open(CLUSTERS_FILE, 'w') as text:
            for cluster in clusters:
                line = '; '.join([str(value) for value in cluster])
                text.write(line + '\n')
        self.compress_file(CLUSTERS_FILE, CLUSTERS_FILE_XZ)

        pkgs_clusters = "vim-0:1;2:1\n" \
                        "python-1:1\n" \
                        "ruby-2:1\n" \
                        "gedit-0:1;1:1\n" \
                        "vagrant-1:1;2:1"
        with open(PKGS_CLUSTERS_FILE, 'w') as text:
            text.write(pkgs_clusters)
        self.compress_file(PKGS_CLUSTERS_FILE, PKGS_CLUSTERS_FILE_XZ)

    def create_inrelease_file(self):
        command = "sha256sum {}*.xz > {}".format(COLLABORATIVE_DATA_DIR,
                                                 INRELEASE_FILE)
        commands.getoutput(command)

    @patch('apprecommender.collaborative_data.PopconSubmission.'
           'get_submission_pkgs')
    def test_load_collaborative_by_files(self, mock_submission_pkgs):
        mock_submission_pkgs.return_value = ['vim', 'gedit']

        self.create_collaborative_data_dir()
        self.create_inrelease_file()

        popcon_submission = PopconSubmission()
        submission_pkgs = popcon_submission.get_submission_pkgs()
        collaborative = CollaborativeData.load(COLLABORATIVE_DATA_DIR,
                                               submission_pkgs)
        shutil.rmtree(COLLABORATIVE_DATA_DIR)

        self.assertEqual(['ruby', 'vagrant', 'vim'],
                         sorted(collaborative.user_cluster_pkgs))
        self.assertEqual([1, 0, 0, 1, 0], collaborative.user)
        self.assertEqual(2, collaborative.user_cluster_index)
