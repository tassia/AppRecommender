#!/usr/bin/env python

import numpy as np
import pickle
import re
import os

from scipy import spatial


class KnnLoader:

    def __init__(self, folder_path):
        self.set_folder(folder_path)

    def set_folder(self, folder_path):
        if folder_path[-1] != '/':
            folder_path += '/'

        self.folder_path = os.path.expanduser(folder_path)
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
            pkgs_clusters[pkg] = {int(cluster): int(times) for cluster, times in (cluster_time.split(':') for cluster_time in clusters_times)}

        return pkgs_clusters
