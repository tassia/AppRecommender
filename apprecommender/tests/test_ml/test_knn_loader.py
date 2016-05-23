#!/usr/bin/env python

import os
import pickle
import unittest

from apprecommender.ml.knn_loader import KnnLoader


class KnnLoaderTests(unittest.TestCase):

    KNN_DATA_FILE = 'knn_data'
    USER_POPCON_FILE = 'popcon_for_test'

    def create_knn_data_file(self):
        all_pkgs = ['vim', 'python', 'ruby', 'gedit', 'vagrant']
        users = [[1, 0, 0, 1, 0],
                 [0, 1, 0, 1, 1],
                 [1, 0, 1, 0, 1]]
        clusters = [[1.0, 0.0, 1.0, 0.0, 1.0],
                    [0.0, 1.0, 0.0, 1.0, 1.0],
                    [1.0, 0.0, 0.0, 1.0, 0.0]]
        users_clusters = [2, 1, 0]

        saved_data = {'all_pkgs': all_pkgs, 'clusters': clusters,
                      'users': users, 'users_clusters': users_clusters}

        with open(KnnLoaderTests.KNN_DATA_FILE, 'wb') as text:
            pickle.dump(saved_data, text)

    def create_user_popcon_file(self):
        popcon_header = 'POPULARITY-CONTEST-0 TIME:370542026 ID:1popcon' \
                        'ARCH:amd64 POPCONVER: VENDOR:Debian\n'

        with open(KnnLoaderTests.USER_POPCON_FILE, 'wb') as text:
            text.write(popcon_header)
            text.write('15019500 154428337 vim /usr/bin/vim\n')
            text.write('15019500 154428337 gedit /usr/bin/gedit\n')
            text.write('END-POPULARITY-CONTEST-0 TIME:1464009355\n')

    def test_load_knn_by_files(self):
        self.create_knn_data_file()
        self.create_user_popcon_file()

        knn = KnnLoader.load(KnnLoaderTests.KNN_DATA_FILE,
                             KnnLoaderTests.USER_POPCON_FILE)
        os.remove(KnnLoaderTests.KNN_DATA_FILE)
        os.remove(KnnLoaderTests.USER_POPCON_FILE)

        self.assertEqual([['vim', 'gedit']], knn.submissions)
        self.assertEqual([1, 0, 0, 1, 0], knn.user)
        self.assertEqual(2, knn.user_cluster_index)
