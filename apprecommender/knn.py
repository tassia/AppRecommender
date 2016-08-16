#!/usr/bin/env python

import hashlib
import lzma
import os
import re
import shutil
import wget

import numpy as np

from scipy import spatial
from apprecommender.config import Config


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

        match = re.compile(r'^\d+\s\d+\s([^\/\s]+)(?!.*<NOFILES>)',
                           re.MULTILINE)
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


class KnnError(Exception):

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return self.value


class KnnDownloadData:

    def __init__(self, save_data_folder):
        download_folder_link = Config().popcon_folder_link

        self.save_data_folder = save_data_folder
        self.inrelease_link = os.path.join(download_folder_link,
                                           '0688/InRelease')
        self.clusters_link = os.path.join(download_folder_link,
                                          '0687/clusters.xz')
        self.pkgs_clusters_link = os.path.join(download_folder_link,
                                               '0689/pkgs_clusters.xz')

    def download(self):
        if not os.path.exists(self.save_data_folder):
            os.mkdir(self.save_data_folder)

        self.download_files()
        self.check_sha256sum()
        self.move_files_to_save_data_folder()

    def download_files(self):
        links = [self.inrelease_link, self.clusters_link,
                 self.pkgs_clusters_link]

        try:
            files = []
            for link in links:
                files.append(wget.download(link, bar=None))

            return files
        except IOError:
            raise KnnError("Error: link not founded: {}".format(link))

    def check_sha256sum(self):
        sha_text = self.get_sha256sum_text()
        ifile = open('InRelease', 'r')
        inrelease_text = ifile.read()
        ifile.close()

        files_sha = self.get_sha256_from_text(sha_text)
        inrelease = self.get_sha256_from_text(inrelease_text)

        if files_sha != inrelease:
            error_msg = "Error: Checksum of collaborative data its wrong."
            raise KnnError(error_msg)

    def get_sha256sum_text(self):
        files = ['clusters.xz', 'pkgs_clusters.xz']

        sha256sum = ''
        for file_name in files:
            ifile = open(file_name, 'rb')
            content = ifile.read()
            ifile.close()

            checksum = hashlib.sha256(content).hexdigest()

            sha256sum += '{}  {}\n'.format(checksum, file_name)

        sha256sum = sha256sum[:-1]

        return sha256sum

    def get_sha256_from_text(self, text):
        match_sha = re.compile(r'^([^\s]+).+\w.xz', re.MULTILINE)
        match_file = re.compile(r'(\w+.xz)$', re.MULTILINE)

        files = match_file.findall(text)
        sha256s = match_sha.findall(text)
        files_sha = {ifile: sha for ifile, sha in zip(files, sha256s)}

        return files_sha

    def move_files_to_save_data_folder(self):
        files = ['InRelease', 'clusters.xz', 'pkgs_clusters.xz']

        for file_name in files:
            file_path = os.path.join(self.save_data_folder, file_name)

            if os.path.exists(file_path):
                os.remove(file_path)

            shutil.move(file_name, file_path)


class KnnLoader:

    def __init__(self, folder_path):
        self.set_folder(folder_path)
        self.set_files_path()
        self.load_files_content()

    def set_folder(self, folder_path):
        folder_path = os.path.expanduser(folder_path)
        self.folder_path = os.path.abspath(folder_path)

        if self.folder_path[-1] != '/':
            self.folder_path += '/'

    def check_file_exists(self, file_path):
        file_name = os.path.basename(file_path)
        error_msg = "Error on collaborative data. File not founded: {}"
        if not os.path.exists(file_path):
            raise KnnError(error_msg.format(file_name))

    def set_files_path(self):
        self.clusters_path = self.folder_path + 'clusters.xz'
        self.inrelease_path = self.folder_path + 'InRelease'
        self.pkgs_clusters_path = self.folder_path + 'pkgs_clusters.xz'

        self.check_file_exists(self.clusters_path)
        self.check_file_exists(self.inrelease_path)
        self.check_file_exists(self.pkgs_clusters_path)

    def get_compressed_file_text(self, file_path):
        ifile = lzma.LZMAFile(file_path)
        text = ifile.read().decode('utf-8')
        ifile.close()

        return text

    def load_files_content(self):
        self.clusters_content = self.get_compressed_file_text(
            self.clusters_path)
        self.pkgs_cluster_content = self.get_compressed_file_text(
            self.pkgs_clusters_path)

    def load_all_pkgs(self):
        match = re.compile(r'^(.*)-', re.MULTILINE)
        all_pkgs = match.findall(self.pkgs_cluster_content)

        return all_pkgs

    def load_clusters(self):
        clusters = []
        clusters = [map(float, line.strip().split(';'))
                    for line in self.clusters_content.splitlines()]

        return clusters

    def load_pkgs_clusters(self):
        pkgs_match = re.compile(r'^(.*)-', re.MULTILINE)
        clusters_match = re.compile(r'^.*-(.*)', re.MULTILINE)

        pkgs = pkgs_match.findall(self.pkgs_cluster_content)
        clusters_list = clusters_match.findall(self.pkgs_cluster_content)

        pkgs_clusters = {}
        for index, pkg in enumerate(pkgs):
            clusters_times = clusters_list[index].split(';')
            pkgs_clusters[pkg] = {int(cluster): int(times)
                                  for cluster, times in
                                  (cluster_time.split(':')
                                   for cluster_time in clusters_times)}

        return pkgs_clusters
