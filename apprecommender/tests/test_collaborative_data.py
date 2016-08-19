#!/usr/bin/env python

import commands
import lzma
import os
import shutil
import unittest

from apprecommender.collaborative_data import CollaborativeData


COLLABORATIVE_DATA_DIR = 'apprecommender/tests/test_data/' \
                         '.popcon_clusters_tests/'
USER_POPCON_FILE = COLLABORATIVE_DATA_DIR + 'popcon_for_test'
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

    def create_user_popcon_file(self):
        popcon_header = 'POPULARITY-CONTEST-0 TIME:370542026 ID:1popcon' \
                        'ARCH:amd64 POPCONVER: VENDOR:Debian\n'

        with open(USER_POPCON_FILE, 'wb') as text:
            text.write(popcon_header)
            text.write('15019500 154428337 vim /usr/bin/vim\n')
            text.write('15019500 154428337 gedit /usr/bin/gedit\n')
            text.write('END-POPULARITY-CONTEST-0 TIME:1464009355\n')

    def create_inrelease_file(self):
        command = "sha256sum {}*.xz > {}".format(COLLABORATIVE_DATA_DIR,
                                                 INRELEASE_FILE)
        commands.getoutput(command)

    def test_load_collaborative_by_files(self):
        self.create_collaborative_data_dir()
        self.create_user_popcon_file()
        self.create_inrelease_file()

        collaborative = CollaborativeData.load(COLLABORATIVE_DATA_DIR,
                                               USER_POPCON_FILE)
        shutil.rmtree(COLLABORATIVE_DATA_DIR)

        self.assertEqual(['ruby', 'vagrant', 'vim'],
                         sorted(collaborative.user_cluster_pkgs))
        self.assertEqual([1, 0, 0, 1, 0], collaborative.user)
        self.assertEqual(2, collaborative.user_cluster_index)
