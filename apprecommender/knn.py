#!/usr/bin/env python

import commands
import os
import re

import numpy as np

from scipy import spatial


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


class KnnLoader:

    def __init__(self, folder_path):
        self.set_folder(folder_path)
        self.check_sha256()
        self.set_files_path()

    def check_sha256(self):
        sha_text = commands.getoutput("sha256sum %s*.txt" % self.folder_path)
        ifile = open(self.folder_path + 'InRelease', 'r')
        inrelease_text = ifile.read()
        ifile.close()

        files_sha = self.get_files_sha(sha_text)
        inrelease = self.get_files_sha(inrelease_text)

        if files_sha != inrelease:
            raise Exception("Check sha256sum its WRONG on folder: %s" %
                            self.folder_path)

        return files_sha == inrelease

    def get_files_sha(self, text):
        match_sha = re.compile(r'^([^\s]+).+\w.txt', re.MULTILINE)
        match_file = re.compile(r'(\w+.txt)$', re.MULTILINE)

        files = match_file.findall(text)
        sha256s = match_sha.findall(text)
        files_sha = {ifile: sha for ifile, sha in zip(files, sha256s)}

        return files_sha

    def set_folder(self, folder_path):
        if folder_path[-1] != '/':
            folder_path += '/'

        self.folder_path = os.path.expanduser(folder_path)

    def set_files_path(self):
        self.pkgs_clusters_path = self.folder_path + 'pkgs_clusters.txt'
        self.clusters_path = self.folder_path + 'clusters.txt'

    def load_all_pkgs(self):
        match = re.compile(r'^(.*)-', re.MULTILINE)
        ifile = open(self.pkgs_clusters_path)
        text = ifile.read()
        ifile.close()

        all_pkgs = match.findall(text)

        return all_pkgs

    def load_clusters(self):
        clusters = []
        with open(self.clusters_path, 'r') as text:
            clusters = [map(float, line.strip().split(';')) for line in text]

        return clusters

    def load_pkgs_clusters(self):
        pkgs_match = re.compile(r'^(.*)-', re.MULTILINE)
        clusters_match = re.compile(r'^.*-(.*)', re.MULTILINE)

        ifile = open(self.pkgs_clusters_path)
        text = ifile.read()
        ifile.close()

        pkgs = pkgs_match.findall(text)
        clusters_list = clusters_match.findall(text)

        pkgs_clusters = {}
        for index, pkg in enumerate(pkgs):
            clusters_times = clusters_list[index].split(';')
            pkgs_clusters[pkg] = {int(cluster): int(times)
                                  for cluster, times in
                                  (cluster_time.split(':')
                                   for cluster_time in clusters_times)}

        return pkgs_clusters
