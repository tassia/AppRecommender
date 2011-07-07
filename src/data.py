#!/usr/bin/env python
"""
    data - python module for data sources classes and methods.
"""
__author__ = "Tassia Camoes Araujo <tassia@gmail.com>"
__copyright__ = "Copyright (C) 2011 Tassia Camoes Araujo"
__license__ = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import gc
import xapian
import logging
import random
import cluster
import shutil

from error import Error
from singleton import Singleton
from dissimilarity import *

def axi_search_pkgs(axi,pkgs_list):
    terms = ["XP"+item for item in pkgs_list]
    query = xapian.Query(xapian.Query.OP_OR, terms)
    enquire = xapian.Enquire(axi)
    enquire.set_query(query)
    matches = enquire.get_mset(0,axi.get_doccount())
    return matches

def axi_search_pkg_tags(axi,pkg):
    query = xapian.Query(xapian.Query.OP_OR, "XP"+pkg)
    enquire = xapian.Enquire(axi)
    enquire.set_query(query)
    matches = enquire.get_mset(0,1)
    for m in matches:
        tags = [term.term for term in axi.get_document(m.docid).termlist() if
                term.term.startswith("XT")]
    return tags

def print_index(index):
    output = "\n---\n" + xapian.Database.__repr__(index) + "\n---\n"
    for term in index.allterms():
        output += term.term+"\n"
        output += str([index.get_document(posting.docid).get_data()
                       for posting in index.postlist(term.term)])
        output += "\n---"
    return output

class SampleAptXapianIndex(xapian.WritableDatabase):
    """
    Sample data source for packages information, mainly useful for tests.
    """
    def __init__(self,pkgs_list,axi,path):
        xapian.WritableDatabase.__init__(self,path,
                                         xapian.DB_CREATE_OR_OVERWRITE)
        sample = axi_search_pkgs(axi,pkgs_list)
        for package in sample:
            doc_id = self.add_document(axi.get_document(package.docid))

    def __str__(self):
        return print_index(self)

class PopconSubmission():
    def __init__(self,path,user_id=0):
        self.packages = dict()
        self.path = path
        self.load()
        if user_id:
            self.user_id = user_id

    def __str__(self):
        output = "\nPopularity-contest submission ID "+self.user_id
        for pkg, weight in self.packages.items():
            output += "\n "+pkg+": "+str(weight)
        return output

    def load(self,binary=1):
    	"""
    	Parse a popcon submission, generating the names of the valid packages
        in the vote.
    	"""
        with open(self.path) as submission:
    	    for line in submission:
                if line.startswith("POPULARITY"):
                    self.user_id = line.split()[2].lstrip("ID:")
                elif not line.startswith("END-POPULARITY"):
                    data = line.rstrip('\n').split()
                    if len(data) > 2:
                        pkg = data[2]
                        if len(data) > 3:
                            exec_file = data[3]
                            # Binary weight
                            if binary:
                                self.packages[pkg] = 1
                            # Weights inherited from Enrico's anapop
                            # No executable files to track
                            elif exec_file == '<NOFILES>':
                                self.packages[pkg] = 1
                            # Recently used packages
                            elif len(data) == 4:
                                self.packages[pkg] = 10
                            # Unused packages
                            elif data[4] == '<OLD>':
                                self.packages[pkg] = 3
                            # Recently installed packages
                            elif data[4] == '<RECENT-CTIME>':
                                self.packages[pkg] = 8

class PopconXapianIndex(xapian.WritableDatabase):
    """
    Data source for popcon submissions defined as a singleton xapian database.
    """
    def __init__(self,cfg,reindex=0,recluster=0):
        """
        Set initial attributes.
        """
        self.axi = xapian.Database(cfg.axi)
        self.path = os.path.expanduser(cfg.popcon_index)
        if reindex or not self.load_index():
            if not os.path.exists(cfg.popcon_dir):
                os.makedirs(cfg.popcon_dir)
            if not os.listdir(cfg.popcon_dir):
                logging.critical("Popcon dir seems to be empty.")
                raise Error
            if not cfg.clustering:
                self.source_dir = os.path.expanduser(cfg.popcon_dir)
            else:
                self.source_dir = os.path.expanduser(cfg.clusters_dir)
                if not os.path.exists(cfg.clusters_dir):
                    os.makedirs(cfg.clusters_dir)
                if not os.listdir(cfg.clusters_dir):
                    distance = JaccardDistance()
                    logging.info("Clustering popcon submissions from \'%s\'"
                                 % cfg.popcon_dir)
                    logging.info("Clusters will be placed at \'%s\'"
                                 % cfg.clusters_dir)
                    data = self.get_submissions(cfg.popcon_dir)
                    if cfg.clustering == "Hierarchical":
                        self.hierarchical_clustering(data,cfg.clusters_dir,
                                                     distance)
                    else:
                        self.kmedoids_clustering(data,cfg.clusters_dir,
                                                 distance)
            self.build_index()

    def __str__(self):
        return print_index(self)

    def load_index(self):
        """
        Load an existing popcon index.
        """
        try:
            logging.info("Opening existing popcon xapian index at \'%s\'"
                          % self.path)
            xapian.Database.__init__(self,self.path)
        except xapian.DatabaseError:
            logging.info("Could not open popcon index.")
            return 0

    def build_index(self):
        """
        Create a xapian index for popcon submissions at 'source_dir' and
        place it at 'self.path'.
        """
        shutil.rmtree(self.path,1)
        os.makedirs(self.path)

        try:
            logging.info("Indexing popcon submissions from \'%s\'" %
                         self.source_dir)
            logging.info("Creating new xapian index at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self,self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError:
            logging.critical("Could not create popcon xapian index.")
            raise Error

        for root, dirs, files in os.walk(self.source_dir):
            for popcon_file in files:
                submission = PopconSubmission(os.path.join(root, popcon_file))
                doc = xapian.Document()
                doc.set_data(submission.user_id)
                logging.debug("Parsing popcon submission \'%s\'" %
                              submission.user_id)
                for pkg, freq in submission.packages.items():
                    doc.add_term("XP"+pkg,freq)
                    for tag in axi_search_pkg_tags(self.axi,pkg):
                        doc.add_term(tag,freq)
                doc_id = self.add_document(doc)
                logging.debug("Popcon Xapian: Indexing doc %d" % doc_id)
            # python garbage collector
        	gc.collect()
        # flush to disk database changes
        self.commit()

    def get_submissions(self,submissions_dir):
        """
        Get popcon submissions from popcon_dir
        """
        submissions = []
        for root, dirs, files in os.walk(submissions_dir):
            for popcon_file in files:
                submission = PopconSubmission(os.path.join(root, popcon_file))
                submissions.append(submission)
        return submissions

    def hierarchical_clustering(self,data,clusters_dir,distance,k=10):
        """
        Select popcon submissions from popcon_dir and place them at clusters_dir
        """
        cl = cluster.HierarchicalClustering(data, lambda x,y:
                                                  distance(x.packages.keys(),
                                                           y.packages.keys()))
        clusters = cl.getlevel(0.5)
        for c in clusters:
            print "cluster"
            for submission in c:
                print submission.user_id

    def kmedoids_clustering(self,data,clusters_dir,distance,k=10):
        clusters = KMedoidsClustering(data,lambda x,y:
                                           distance(x.packages.keys(),
                                                    y.packages.keys()))
        medoids = clusters.getMedoids(2)
        for submission in medoids:
            shutil.copyfile(submission.path,os.path.join(clusters_dir,
                                                         submission.user_id))

class KMedoidsClustering(cluster.KMeansClustering):

    def __init__(self,data,distance):
        if len(data)<100:
            data_sample = data
        else:
            data_sample = random.sample(data,100)
        cluster.KMeansClustering.__init__(self, data_sample, distance)
        self.distanceMatrix = {}
        for submission in self._KMeansClustering__data:
            self.distanceMatrix[submission.user_id] = {}

    def loadDistanceMatrix(self,cluster):
        for i in range(len(cluster)-1):
            for j in range(i+1,len(cluster)):
                try:
                    d = self.distanceMatrix[cluster[i].user_id][cluster[j].user_id]
                    logging.debug("Using d[%d,%d]" % (i,j))
                except:
                    d = self.distance(cluster[i],cluster[j])
                    self.distanceMatrix[cluster[i].user_id][cluster[j].user_id] = d
                    self.distanceMatrix[cluster[j].user_id][cluster[i].user_id] = d
                    logging.debug("d[%d,%d] = %.2f" % (i,j,d))

    def getMedoid(self,cluster):
        """
        Return the medoid popcon submission of a given a cluster, based on
        the distance function.
        """
        logging.debug("Cluster size: %d" % len(cluster))
        self.loadDistanceMatrix(cluster)
        medoidDistance = sys.maxint
        for i in range(len(cluster)):
            totalDistance = sum(self.distanceMatrix[cluster[i].user_id].values())
            print "totalDistance[",i,"]=",totalDistance
            if totalDistance < medoidDistance:
                medoidDistance = totalDistance
                medoid = i
            print "medoidDistance:",medoidDistance
        logging.debug("Cluster medoid: [%d] %s" % (medoid,
                                                   cluster[medoid].user_id))
        return cluster[medoid]

    def assign_item(self, item, origin):
        """
        Assigns an item from a given cluster to the closest located cluster
        """
        closest_cluster = origin
        for cluster in self._KMeansClustering__clusters:
            if self.distance(item,self.getMedoid(cluster)) < self.distance(item,self.getMedoid(closest_cluster)):
                closest_cluster = cluster

        if closest_cluster != origin:
            self.move_item(item, origin, closest_cluster)
            logging.debug("Item changed cluster: %s" % item.user_id)
            return True
        else:
            return False

    def getMedoids(self,n):
        """
        Generate n clusters and return their medoids.
        """
        medoids = [self.getMedoid(cluster) for cluster in self.getclusters(n)]
        logging.info("Clustering completed and the following centroids were found: %s" % [c.user_id for c in medoids])
        return medoids
