#!/usr/bin/env python

import numpy as np
import pickle
import re

from scipy import spatial


class KnnLoader:

    def __init__(self, popcon_clusters_path):
        self.file_path = popcon_clusters_path
        self.all_pkgs_path = self.file_path + 'all_pkgs.txt'
        self.clusters_path = self.file_path + 'clusters.txt'
        self.users_clusters_path = self.file_path + 'users_clusters.txt'
        self.users_path = self.file_path + 'users/user_{}.txt'

    def all_pkgs(self):
        all_pkgs = []
        with open(self.all_pkgs_path, 'r') as text:
            all_pkgs = [line.strip() for line in text]

        return all_pkgs

    def clusters(self):
        clusters = []
        with open(self.clusters_path, 'r') as text:
            clusters = [map(float, line.strip().split(';')) for line in text]

        return clusters

    def users_clusters(self):
        users_clusters = {}
        with open(self.users_clusters_path, 'r') as text:
            users_clusters = [int(cluster_index) for _, cluster_index in
                              (line.split(':') for line in text)]

        return users_clusters

    def users(self, indices):
        users_paths = []
        for index in indices:
            user_path = self.users_path.format(index)
            users_paths.append(user_path)

        users = []
        for user_path in users_paths:
            with open(user_path, 'r') as text:
                user = [line.strip() for line in text]
                users.append(user)

        return users
