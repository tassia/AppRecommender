#!/usr/bin/env python

import numpy as np
import re
import os

from scipy import spatial
from apprecommender.ml.knn_loader import KnnLoader


class Knn:

    @staticmethod
    def load(load_data_path, user_popcon_file_path):
        knn = Knn()
        knn_loader = KnnLoader(load_data_path)

        knn.all_pkgs = knn_loader.load_all_pkgs()
        knn.clusters = knn_loader.load_clusters()
        knn.pkgs_clusters = knn_loader.load_pkgs_clusters()

        knn.load_user_popcon_file(user_popcon_file_path)

        return knn

    def __init__(self):
        self.user = None
        self.user_cluster_pkgs = {}
        self.user_cluster_index = None

    def read_popcon_file(self, file_path):
        file_path = os.path.expanduser(file_path)

        match = re.compile(r'^\d+\s\d+\s([^\/\s]+)', re.MULTILINE)
        ifile = open(file_path)
        text = ifile.read()
        ifile.close()

        popcon_entry = match.findall(text)

        return popcon_entry

    def create_user(self, popcon_file_path):
        popcon_entry = self.read_popcon_file(popcon_file_path)
        self.user = [0 for x in range(len(self.all_pkgs))]

        for pkg_index, pkg in enumerate(self.all_pkgs):
            if pkg in popcon_entry:
                self.user[pkg_index] = 1

        return self.user

    def create_user_cluster_index(self):
        np_clusters = np.array(self.clusters)
        query = spatial.KDTree(np_clusters).query(self.user)[1]
        cluster = np_clusters[query].tolist()
        self.user_cluster_index = self.clusters.index(cluster)

    def create_user_cluster_pkgs(self):
        cluster = self.user_cluster_index
        self.user_cluster_pkgs = [pkg for pkg, clusters in
                                  self.pkgs_clusters.iteritems()
                                  if cluster in clusters]

    def create_users_submissions_by_user_cluster(self):
        np_users_clusters = np.array(self.users_clusters)
        index = self.user_cluster_index
        users_indices = np.where(np_users_clusters == index)[0].tolist()
        self.submissions = self.loader.users(users_indices)

    def load_user_popcon_file(self, popcon_file_path):
        self.create_user(popcon_file_path)
        self.create_user_cluster_index()
        self.create_user_cluster_pkgs()
