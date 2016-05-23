#!/usr/bin/env python

import numpy as np
import pickle
import re

from scipy import spatial


class KnnLoader:
    '''
    This class contains the implementation of load knn data on pickle format.
    '''

    '''
    Loaded data:     The file to load data must have a pickle with a hash,
                     this hash must have the following keys:
                     all_pkgs, users, clusters and users_clusters

    all_pkgs:        List with all packages of users, without duplication of
                     the packages, exemple: ['vim', 'python', 'ruby'].

    users:           Its a list when each element is a list, that the second
                     list represents an user, where each element of the second
                     list is a binary value which indicates if the user has a
                     package in the same column of the 'all_pkgs' list.

                     Exemple:

                     all_pkgs: ['vim', 'python', 'ruby', 'gedit', 'vagrant']

                     users:  [ [  1  ,    0    ,   0   ,    1   ,     0    ]
                               [  0  ,    1    ,   0   ,    1   ,     1    ]
                               [  1  ,    0    ,   1   ,    0   ,     1    ] ]

    clusters:        Its a list of clusters, where each cluster its a list
                     with the same size of the 'all_pkgs' list, where the
                     cluster list represents the cluster position on chart.

    users_clusters:  List when each element represents a line of 'users', and
                     each value its the index of cluster in the 'clusters'
                     list.
    '''

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

    def create_users_submissions_by_user_cluster(self):
        np_users_clusters = np.array(self.users_clusters)
        index = self.user_cluster_index
        users_indices = np.where(np_users_clusters == index)[0].tolist()
        users = np.matrix(self.users_pkgs)[users_indices, :].tolist()

        self.submissions = []
        for user in users:
            submission = []
            for index, pkg in enumerate(self.all_pkgs):
                if user[index] is 1:
                    submission.append(pkg)

            self.submissions.append(submission)

    def load_user_popcon_file(self, popcon_file_path):
        self.create_user(popcon_file_path)
        self.create_user_cluster_index()
        self.create_users_submissions_by_user_cluster()
