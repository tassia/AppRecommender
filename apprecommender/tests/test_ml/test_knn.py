#!/usr/bin/env python

import os
import shutil
import unittest

from apprecommender.ml.knn import Knn


class KnnTests(unittest.TestCase):

    KNN_DATA_DIR = "apprecommender/tests/test_data/.popcon_clusters_tests/"
    USER_POPCON_FILE = 'popcon_for_test'

    def create_KNN_DATA_DIRs(self):
        dir_name = KnnTests.KNN_DATA_DIR
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
        os.mkdir(dir_name)

        all_pkgs = ['vim', 'python', 'ruby', 'gedit', 'vagrant']
        all_pkgs_file = dir_name + 'all_pkgs.txt'
        with open(all_pkgs_file, 'w') as text:
            for pkg in all_pkgs:
                text.write(pkg + '\n')

        users = [['vim', 'gedit'],
                 ['python', 'gedit', 'vagrant'],
                 ['vim', 'ruby', 'vagrant']]
        users_dir = dir_name + 'users/'
        os.mkdir(users_dir)
        user_file = users_dir + 'user_{}.txt'
        for index, user_pkgs in enumerate(users):
            with open(user_file.format(index), 'w') as text:
                for pkg in user_pkgs:
                    text.write(pkg + '\n')

        clusters = [[1.0, 0.0, 1.0, 0.0, 1.0],
                    [0.0, 1.0, 0.0, 1.0, 1.0],
                    [1.0, 0.0, 0.0, 1.0, 0.0]]
        clusters_file = dir_name + 'clusters.txt'
        with open(clusters_file, 'w') as text:
            for cluster in clusters:
                line = '; '.join([str(value) for value in cluster])
                text.write(line + '\n')

        users_clusters = [2, 1, 0]
        users_clusters_file = dir_name + 'users_clusters.txt'
        with open(users_clusters_file, 'w') as text:
            for index, user_cluster in enumerate(users_clusters):
                line = "{}: {}".format(index, user_cluster)
                text.write(line + '\n')

    def create_user_popcon_file(self):
        popcon_header = 'POPULARITY-CONTEST-0 TIME:370542026 ID:1popcon' \
                        'ARCH:amd64 POPCONVER: VENDOR:Debian\n'

        with open(KnnTests.USER_POPCON_FILE, 'wb') as text:
            text.write(popcon_header)
            text.write('15019500 154428337 vim /usr/bin/vim\n')
            text.write('15019500 154428337 gedit /usr/bin/gedit\n')
            text.write('END-POPULARITY-CONTEST-0 TIME:1464009355\n')

    def test_load_knn_by_files(self):
        self.create_KNN_DATA_DIRs()
        self.create_user_popcon_file()

        knn = Knn.load(KnnTests.KNN_DATA_DIR,
                       KnnTests.USER_POPCON_FILE)
        shutil.rmtree(KnnTests.KNN_DATA_DIR)
        os.remove(KnnTests.USER_POPCON_FILE)

        self.assertEqual([['vim', 'gedit']], knn.submissions)
        self.assertEqual([1, 0, 0, 1, 0], knn.user)
        self.assertEqual(2, knn.user_cluster_index)
