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
import re
import xapian
import axi
from debian import debtags
import logging
import hashlib

from error import Error
from singleton import Singleton
import cluster
from similarity import *

class Item:
    """
    Generic item definition.
    """

class Package(Item):
    """
    Definition of a GNU/Linux application as a recommender item.
    """
    def __init__(self,package_name):
        """
        Set initial attributes.
        """
        self.package_name  = package_name

def normalize_tags(string):
    """
    Substitute string characters : by _ and - by '.
    Examples:
        admin::package-management   ->   admin__package'management
        implemented-in::c++         ->   implemented-in__c++
    """
    return string.replace(':','_').replace('-','\'')

def load_debtags_db(db_path):
    """
    Load debtags database from the source file.
    """
    tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
    try:
        db_file = open(db_path, "r")
        debtags_db = debtags.DB()
        debtags_db.read(db_file,lambda x: not tag_filter.match(x))
        db_file.close()
        return debtags_db
    except:
        logging.error("Could not load DebtagsDB from '%s'." % self.db_path)
        raise Error

class TagsXapianIndex(xapian.WritableDatabase,Singleton):
    """
    Data source for tags info defined as a singleton xapian database.
    """
    def __init__(self,cfg):
        """
        Set initial attributes.
        """
        self.path = os.path.expanduser(cfg.tags_index)
        self.db_path = os.path.expanduser(cfg.tags_db)
        self.debtags_db = debtags.DB()

        try:
            db_file = open(self.db_path)
        except IOError:
            logging.error("Could not load DebtagsDB from '%s'." % self.db_path)
            raise Error
        md5 = hashlib.md5()
        md5.update(db_file.read())
        self.db_md5 = md5.hexdigest()
        db_file.close()
        self.load_index(cfg.reindex)

#    def load_db(self):
#        """
#        Load debtags database from the source file.
#        """
#        tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
#        try:
#            db_file = open(self.db_path, "r")
#            self.debtags_db.read(db_file,lambda x: not tag_filter.match(x))
#            db_file.close()
#        except:
#            logging.error("Could not load DebtagsDB from '%s'." % self.db_path)
#            raise Error

    def relevant_tags_from_db(self,pkgs_list,qtd_of_tags):
        """
        Return most relevant tags considering a list of packages.
        """
        if not self.debtags_db.package_count():
            self.debtags_db = load_debtags_db(self.db_path)
        relevant_db = self.debtags_db.choose_packages(pkgs_list)
        relevance_index = debtags.relevance_index_function(self.debtags_db,
                                                           relevant_db)
        sorted_relevant_tags = sorted(relevant_db.iter_tags(),
                                      lambda a, b: cmp(relevance_index(a),
                                      relevance_index(b)))
        return normalize_tags(' '.join(sorted_relevant_tags[-qtd_of_tags:]))

    def load_index(self,reindex):
        """
        Load an existing debtags index.
        """
        if not reindex:
            try:
                logging.info("Opening existing debtags xapian index at \'%s\'"
                              % self.path)
                xapian.Database.__init__(self,self.path)
                md5 = self.get_metadata("md5")
                if not md5 == self.db_md5:
                    logging.info("Index must be updated.")
                    reindex = 1
            except xapian.DatabaseError:
                logging.info("Could not open debtags index.")
                reindex =1

        if reindex:
            self.new_index()

    def new_index(self):
        """
        Create a xapian index for debtags info based on 'debtags_db' and
        place it at 'self.path'.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        try:
            logging.info("Indexing debtags info from \'%s\'" %
                         self.db_path)
            logging.info("Creating new xapian index at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self,self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError:
            logging.critical("Could not create xapian index.")
            raise Error

        self.debtags_db = load_debtags_db(self.db_path)
        self.set_metadata("md5",self.db_md5)

        for pkg,tags in self.debtags_db.iter_packages_tags():
            doc = xapian.Document()
            doc.set_data(pkg)
            for tag in tags:
                doc.add_term(normalize_tags(tag))
            doc_id = self.add_document(doc)
            logging.debug("Debtags Xapian: Indexing doc %d",doc_id)

class PopconXapianIndex(xapian.WritableDatabase,Singleton):
    """
    Data source for popcon submissions defined as a singleton xapian database.
    """
    def __init__(self,cfg):
        """
        Set initial attributes.
        """
        self.path = os.path.expanduser(cfg.popcon_index)
        self.popcon_dir = os.path.expanduser(cfg.popcon_dir)
        self.debtags_path = os.path.expanduser(cfg.tags_db)
        self.load_index()

    def parse_submission(self,submission_path,binary=1):
    	"""
    	Parse a popcon submission, generating the names of the valid packages
        in the vote.
    	"""
        submission = open(submission_path)
    	for line in submission:
            if not line.startswith("POPULARITY"):
                if not line.startswith("END-POPULARITY"):
                    data = line[:-1].split(" ")
                    if len(data) > 3:
                        if binary:
                            # every installed package has the same weight
                            yield data[2], 1
                        elif data[3] == '<NOFILES>':
                            # No executable files to track
                            yield data[2], 1
                        elif len(data) == 4:
                            # Recently used packages
                            yield data[2], 10
                        elif data[4] == '<OLD>':
                            # Unused packages
                            yield data[2], 3
                        elif data[4] == '<RECENT-CTIME>':
                            # Recently installed packages
                            yield data[2], 8

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
            self.new_index()

    def new_index(self):
        """
        Create a xapian index for popcon submissions at 'popcon_dir' and
        place it at 'self.path'.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        debtags_db = load_debtags_db(self.debtags_path)

        try:
            logging.info("Indexing popcon submissions from \'%s\'" %
                         self.popcon_dir)
            logging.info("Creating new xapian index at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self,self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError:
            logging.critical("Could not create popcon xapian index.")
            raise Error

        for root, dirs, files in os.walk(self.popcon_dir):
            for submission in files:
                submission_path = os.path.join(root, submission)
                doc = xapian.Document()
                doc.set_data(submission)
                logging.debug("Parsing popcon submission at \'%s\'" %
                              submission_path)
                for pkg, freq in self.parse_submission(submission_path):
                    doc.add_term(pkg,freq)
                    for tag in debtags_db.tags_of_package(pkg):
                        doc.add_term("XT"+tag,freq)
                doc_id = self.add_document(doc)
                logging.debug("Popcon Xapian: Indexing doc %d" % doc_id)
            # python garbage collector
        	gc.collect()
        # flush to disk database changes
        self.flush()

class PopconSubmission():
    def __init__(self,submission_hash):
        self.hash = submission_hash
        self.pkgs_list = []

    def add_pkg(self,pkg):
        self.pkgs_list.append(pkg)

class PopconClusteredData(Singleton):
    """
    Data source for popcon submissions defined as a singleton xapian database.
    """
    def __init__(self,cfg):
        """
        Set initial attributes.
        """
        self.popcon_dir = os.path.expanduser(cfg.popcon_dir)
        self.clusters_dir = os.path.expanduser(cfg.clusters_dir)
        self.submissions = []
        self.clustering()

    def parse_submission(self,submission_path,binary=1):
    	"""
    	Parse a popcon submission, generating the names of the valid packages
        in the vote.
    	"""
        submission_file = open(submission_path)
    	for line in submission_file:
            if not line.startswith("POPULARITY"):
                if not line.startswith("END-POPULARITY"):
                    data = line[:-1].split(" ")
                    if len(data) > 3:
                        if binary:
                            # every installed package has the same weight
                            yield data[2], 1
                        elif data[3] == '<NOFILES>':
                            # No executable files to track
                            yield data[2], 1
                        elif len(data) == 4:
                            # Recently used packages
                            yield data[2], 10
                        elif data[4] == '<OLD>':
                            # Unused packages
                            yield data[2], 3
                        elif data[4] == '<RECENT-CTIME>':
                            # Recently installed packages
                            yield data[2], 8

    def clustering(self):
        """
        called by init
        Create a xapian index for popcon submissions at 'popcon_dir' and
        place it at 'self.path'.
        """
        if not os.path.exists(self.clusters_dir):
            os.makedirs(self.clusters_dir)

        logging.info("Clustering popcon submissions from \'%s\'" %
                     self.popcon_dir)
        logging.info("Clusters will be placed at \'%s\'" % self.clusters_dir)

        for root, dirs, files in os.walk(self.popcon_dir):
            for submission_hash in files:
                s = PopconSubmission(submission_hash)
                submission_path = os.path.join(root, submission_hash)
                logging.debug("Parsing popcon submission \'%s\'" %
                              submission_hash)
                for pkg, freq in self.parse_submission(submission_path):
                    s.add_pkg(pkg)
                self.submissions.append(s)

        distanceFunction = JaccardIndex()
        cl = cluster.HierarchicalClustering(self.submissions,lambda x,y: distanceFunction(x.pkgs_list,y.pkgs_list))
        clusters = cl.getlevel(0.5)
        for c in clusters:
            print "cluster"
            for submission in c:
                print submission.hash
        #cl = KMeansClusteringPopcon(self.submissions,
        #                            lambda x,y: distanceFunction(x.pkgs_list,y.pkgs_list))
        #clusters = cl.getclusters(2)
        #medoids = cl.getMedoids(2)

class KMedoidsClusteringPopcon(cluster.KMeansClustering):

    def __init__(self,data,distance):
        cluster.KMeansClustering.__init__(self, data, distance)
        self.distanceMatrix = {}
        for submission in self._KMeansClustering__data:
            self.distanceMatrix[submission.hash] = {}

    def loadDistanceMatrix(self,cluster):
        for i in range(len(cluster)-1):
            for j in range(i+1,len(cluster)):
                try:
                    d = self.distanceMatrix[cluster[i].hash][cluster[j].hash]
                    logging.debug("Using d[%d,%d]" % (i,j))
                except:
                    d = self.distance(cluster[i],cluster[j])
                    self.distanceMatrix[cluster[i].hash][cluster[j].hash] = d
                    self.distanceMatrix[cluster[j].hash][cluster[i].hash] = d
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
            totalDistance = sum(self.distanceMatrix[cluster[i].hash].values())
            print "totalDistance[",i,"]=",totalDistance
            if totalDistance < centroidDistance:
                medoidDistance = totalDistance
                medoid = i
            print "medoidDistance:",medoidDistance
        logging.debug("Cluster medoid: [%d] %s" % (medoid, cluster[medoid].hash))
        return cluster[medoid]

    def assign_item(self, item, origin):
        """
        Assigns an item from a given cluster to the closest located cluster

        PARAMETERS
           item   - the item to be moved
           origin - the originating cluster
        """
        closest_cluster = origin
        for cluster in self._KMeansClustering__clusters:
            if self.distance(item,self.getMedoid(cluster)) < self.distance(item,self.getMedoid(closest_cluster)):
                closest_cluster = cluster

        if closest_cluster != origin:
            self.move_item(item, origin, closest_cluster)
            logging.debug("Item changed cluster: %s" % item.hash)
            return True
        else:
            return False

    def getMedoids(self,n):
        """
        Generate n clusters and return their medoids.
        """
        medoids = [self.getMedoid(cluster) for cluster in self.getclusters(n)]
        logging.info("Clustering completed and the following centroids were found: %s" % [c.hash for c in medoids])
        return medoids
