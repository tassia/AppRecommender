#!/usr/bin/env python

import numpy as np
import pickle
import re

from scipy import spatial


class KnnLoader:

    @staticmethod
    def load(knn_file_path, user_popcon_file_path):
        knn = KnnLoader()

        with open(knn_file_path, 'rb') as text:
            loaded_data = pickle.load(text)

            knn.user = None
            knn.all_pkgs = loaded_data['all_pkgs']
            knn.clusters = loaded_data['clusters']
            knn.users_pkgs = loaded_data['users']
            knn.users_clusters = loaded_data['users_clusters']

            knn.load_user_popcon_file(user_popcon_file_path)

        return knn

    def read_popcon_file(self, file_path):
        popcon_entry = []
        with open(file_path, 'r') as text:
            lines = text.readlines()
            for line in lines[1:-1]:
                pkg = line.split()[2]

                if (not re.match(r'^lib.*', pkg) and
                   not re.match(r'.*doc$', pkg) and
                   '/' not in line.split()[2]):
                    popcon_entry.append(pkg)

        return popcon_entry

    def create_user(self, popcon_file_path):
        popcon_entry = self.read_popcon_file(popcon_file_path)
        self.user = [0 for x in range(len(self.all_pkgs))]

        for pkg_index, pkg in enumerate(self.all_pkgs):
            if pkg in popcon_entry:
                self.user[pkg_index] = 1

        return self.user

    def create_user_cluster_index(self):
        query = spatial.KDTree(self.clusters).query(self.user)[1]
        cluster = self.clusters[query]
        self.user_cluster_index = np.where(self.clusters == cluster)[0][0]

    def load_user_popcon_file(self, popcon_file_path):
        self.create_user(popcon_file_path)
        self.create_user_cluster_index()
