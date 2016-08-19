#!/usr/bin/env python

import gnupg
import hashlib
import lzma
import os
import re
import shutil
import subprocess
import wget

import numpy as np

from scipy import spatial
from apprecommender.config import Config


class CollaborativeData:

    """
    This class its used to get the collaborative cluster data and find the
    each cluster the user belongs to

    Attributes:

    user - The packages of user popularity contest submission
    user_cluster_pkgs - The packages in cluster that the user belongs to
    user_cluster_index - The index of cluster that the user belongs to
    """

    @staticmethod
    def load(load_data_path, user_pkgs):
        collaborative = CollaborativeData()
        collaborative_loader = CollaborativeDataLoader(load_data_path)

        collaborative.all_pkgs = collaborative_loader.load_all_pkgs()
        collaborative.clusters = collaborative_loader.load_clusters()
        collaborative.pkgs_clusters = collaborative_loader.load_pkgs_clusters()

        collaborative.load_user_popcon_file(user_pkgs)

        return collaborative

    def __init__(self):
        self.user = None
        self.user_cluster_pkgs = {}
        self.user_cluster_index = None

    def create_user(self, user_pkgs):
        self.user = [0 for x in range(len(self.all_pkgs))]

        for pkg_index, pkg in enumerate(self.all_pkgs):
            if pkg in user_pkgs:
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

    def load_user_popcon_file(self, user_pkgs):
        self.create_user(user_pkgs)
        self.create_user_cluster_index()
        self.create_user_cluster_pkgs()


class PopconSubmission:

    def __init__(self):
        self.pkgs_regex = re.compile(r'^\d+\s\d+\s([^\/\s]+)(?!.*<NOFILES>)',
                                     re.MULTILINE)

    def get_submission_pkgs(self):
        submission = self.generate_submission()

        pkgs = self.pkgs_regex.findall(submission)

        return pkgs

    def generate_submission(self):
        submission = subprocess.check_output('/usr/sbin/popularity-contest',
                                             shell=True)
        return submission


class CollaborativeDataError(Exception):

    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return self.value


class DownloadCollaborativeData:

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

        self.delete_trash_files()
        self.download_files()
        self.check_gpg_signature()
        self.check_sha256sum()
        self.move_files_to_save_data_folder()

    def delete_trash_files(self):
        files = ['InRelease', 'clusters.xz', 'pkgs_clusters.xz']

        for file_name in files:
            if os.path.exists(file_name):
                os.remove(file_name)

    def download_files(self):
        links = [self.inrelease_link, self.clusters_link,
                 self.pkgs_clusters_link]

        try:
            files = []
            for link in links:
                files.append(wget.download(link, bar=None))

            return files
        except IOError:
            message = "Error: link not founded: {}".format(link)
            raise CollaborativeDataError(message)

    def check_gpg_signature(self):
        gnupg_home = '~/.gnupg'
        keyring = Config().popcon_public_key
        gpg = gnupg.GPG(gnupghome=gnupg_home, keyring=keyring)
        gpg.encoding = 'utf-8'

        ifile = open('InRelease', 'r')
        inrelease_data = ifile.read()
        ifile.close()

        if not gpg.verify(inrelease_data).valid:
            message = "Error: The signature of downloaded files are corrupt"
            raise CollaborativeDataError(message)

    def check_sha256sum(self):
        sha_text = self.get_sha256sum_text()
        ifile = open('InRelease', 'r')
        inrelease_text = ifile.read()
        ifile.close()

        files_sha = self.get_sha256_from_text(sha_text)
        inrelease = self.get_sha256_from_text(inrelease_text)

        if files_sha != inrelease or len(files_sha) == 0:
            error_msg = "Error: Checksum of collaborative data its wrong."
            raise CollaborativeDataError(error_msg)

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


class CollaborativeDataLoader:

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
            raise CollaborativeDataError(error_msg.format(file_name))

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
