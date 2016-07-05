#!/usr/bin/env python

import re
import os
import commands


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
