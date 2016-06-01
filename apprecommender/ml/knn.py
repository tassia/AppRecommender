#!/usr/bin/env python

import numpy as np
import re

from scipy import spatial
from apprecommender.ml.knn_loader import KnnLoader


class Knn:
    '''
    Loaded data:     The data to load needs be in a folder, and this folder
                     needs have the following files: all_pkgs, clusters and
                     users_clusters. And this data folder also needs an
                     another folder with name users, that is a folder with
                     users packages

    all_pkgs:        List with all packages of users, without duplication of
                     the packages, exemple: ['vim', 'python', 'ruby'].

    users:           A folder with files when each file contains the user
                     packages.
                     Each file contains the name 'user_[user_index].txt'.

                     Exemple: user_0.txt, user_1.txt, ..., user_10.txt

                     On each file contains a list with packages of the user,
                     when each line contains one package name.

                     Exemple:
                        file - user_0.txt:
                            git
                            vim
                            ruby
                            vagrant

    clusters:        Its a list of clusters, where each cluster its a list
                     with the same size of the 'all_pkgs' list, where the
                     cluster list represents the cluster position on chart.

    users_clusters:  List when each element represents a line of 'users', and
                     each value its the index of cluster in the 'clusters'
                     list.
    '''

    @staticmethod
    def load(load_data_path, user_popcon_file_path):
        knn = Knn()
        knn_loader = KnnLoader(load_data_path)

        knn.all_pkgs = knn_loader.all_pkgs()
        knn.clusters = knn_loader.clusters()
        knn.users_clusters = knn_loader.users_clusters()
        knn.loader = knn_loader

        knn.load_user_popcon_file(user_popcon_file_path)

        return knn

    '''
    Knn attributes:

    user:            Binary list, like user of 'users' into the loaded data,
                     but this is of the AppRecommender user

    submissions:     List of lists with packages of another users with
                     similar profile to the user

                     Exemple:

                     submissions:
                             [ ['vim', 'gedit']
                               ['python', 'gedit', 'vagrant']
                               ['vim', 'ruby', 'vagrant'] ]

    user_cluster_index:  Its the index of cluster in which the user is it,
                         into 'clusters' of the loaded data, t
    '''
    def __init__(self):
        self.user = None
        self.submissions = []
        self.user_cluster_index = None

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
        np_clusters = np.array(self.clusters)
        query = spatial.KDTree(np_clusters).query(self.user)[1]
        cluster = np_clusters[query].tolist()
        self.user_cluster_index = self.clusters.index(cluster)

    def create_users_submissions_by_user_cluster(self):
        np_users_clusters = np.array(self.users_clusters)
        index = self.user_cluster_index
        users_indices = np.where(np_users_clusters == index)[0].tolist()
        self.submissions = self.loader.users(users_indices)

    def load_user_popcon_file(self, popcon_file_path):
        self.create_user(popcon_file_path)
        self.create_user_cluster_index()
        self.create_users_submissions_by_user_cluster()
