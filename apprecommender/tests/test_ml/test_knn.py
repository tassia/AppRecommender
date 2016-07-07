#!/usr/bin/env python

import os
import commands
import shutil
import unittest

from apprecommender.knn import Knn


class KnnTests(unittest.TestCase):

    KNN_DATA_DIR = 'apprecommender/tests/test_data/.popcon_clusters_tests/'
    USER_POPCON_FILE = KNN_DATA_DIR + 'popcon_for_test'
    INRELEASE_FILE = KNN_DATA_DIR + 'InRelease'

    def create_knn_data_dir(self):
        dir_name = KnnTests.KNN_DATA_DIR
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
        os.mkdir(dir_name)

        clusters = [[1.0, 0.0, 1.0, 0.0, 1.0],
                    [0.0, 1.0, 0.0, 1.0, 1.0],
                    [1.0, 0.0, 0.0, 1.0, 0.0]]
        clusters_file = dir_name + 'clusters.txt'
        with open(clusters_file, 'w') as text:
            for cluster in clusters:
                line = '; '.join([str(value) for value in cluster])
                text.write(line + '\n')

        pkgs_clusters = "vim-0:1;2:1\n" \
                        "python-1:1\n" \
                        "ruby-2:1\n" \
                        "gedit-0:1;1:1\n" \
                        "vagrant-1:1;2:1"
        pkgs_clusters_file = dir_name + 'pkgs_clusters.txt'
        with open(pkgs_clusters_file, 'w') as text:
            text.write(pkgs_clusters)

    def create_user_popcon_file(self):
        popcon_header = 'POPULARITY-CONTEST-0 TIME:370542026 ID:1popcon' \
                        'ARCH:amd64 POPCONVER: VENDOR:Debian\n'

        with open(KnnTests.USER_POPCON_FILE, 'wb') as text:
            text.write(popcon_header)
            text.write('15019500 154428337 vim /usr/bin/vim\n')
            text.write('15019500 154428337 gedit /usr/bin/gedit\n')
            text.write('END-POPULARITY-CONTEST-0 TIME:1464009355\n')

    def create_inrelease_file(self):
        command = "sha256sum {}*.txt > {}".format(KnnTests.KNN_DATA_DIR,
                                                  KnnTests.INRELEASE_FILE)
        commands.getoutput(command)

    def test_load_knn_by_files(self):
        self.create_knn_data_dir()
        self.create_user_popcon_file()
        self.create_inrelease_file()

        knn = Knn.load(KnnTests.KNN_DATA_DIR,
                       KnnTests.USER_POPCON_FILE)
        shutil.rmtree(KnnTests.KNN_DATA_DIR)

        self.assertEqual(['ruby', 'vagrant', 'vim'],
                         sorted(knn.user_cluster_pkgs))
        self.assertEqual([1, 0, 0, 1, 0], knn.user)
        self.assertEqual(2, knn.user_cluster_index)
