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
import apt
import re
import operator
import urllib
import simplejson as json

from error import Error
from singleton import Singleton
from dissimilarity import *
from config import Config

def axi_get_pkgs(axi):
    pkgs_names = []
    for docid in range(1,axi.get_lastdocid()+1):
        try:
            doc = axi.get_document(docid)
        except:
            pass
        docterms_XP = [t.term for t in doc.termlist()
                       if t.term.startswith("XP")]
        pkgs_names.append(docterms_XP[0].lstrip('XP'))
    return pkgs_names

def axi_search_pkgs(axi,pkgs_list):
    terms = ["XP"+item for item in pkgs_list]
    query = xapian.Query(xapian.Query.OP_OR, terms)
    enquire = xapian.Enquire(axi)
    enquire.set_query(query)
    mset = enquire.get_mset(0,axi.get_doccount())
    return mset

def axi_search_pkg_tags(axi,pkg):
    enquire = xapian.Enquire(axi)
    enquire.set_query(xapian.Query("XP"+pkg))
    matches = enquire.get_mset(0,1)
    if not matches:
        logging.debug("Package %s not found in items repository" % pkg)
        return False
    for m in matches:
        tags = [term.term for term in axi.get_document(m.docid).termlist() if
                term.term.startswith("XT")]
        if not tags:
            return "notags"
        else:
            return tags

def print_index(index):
    output = "\n---\n" + xapian.Database.__repr__(index) + "\n---\n"
    for term in index.allterms():
        output += term.term+"\n"
        output += str([index.get_document(posting.docid).get_data()
                       for posting in index.postlist(term.term)])
        output += "\n---"
    return output

def tfidf_weighting(index,docs,content_filter,normalized_weigths=0):
    """
    Return a dictionary of terms and weights of all terms of a set of
    documents, based on the frequency of terms in the selected set (docids).
    """
    # Store all terms in one single document
    terms_doc = xapian.Document()
    for d in docs:
        for term in index.get_document(d.docid).termlist():
            if content_filter(term.term):
                if normalized_weigths:
                    terms_doc.add_term(term.term,int(math.ceil(normalized_weigths[d.docid])))
                else:
                    terms_doc.add_term(term.term)
    # Compute sublinear tfidf for each term
    weights = {}
    for term in terms_doc.termlist():
        try:
            # Even if it shouldn't raise error...
            # math.log: ValueError: math domain error
            tf = 1+math.log(term.wdf)
            idf = math.log(index.get_doccount()/
                           float(index.get_termfreq(term.term)))
            weights[term.term] = tf*idf
        except:
            pass
    sorted_weights = list(reversed(sorted(weights.items(),
                                          key=operator.itemgetter(1))))
    #print sorted_weights
    return sorted_weights

def tfidf_plus(index,docs,content_filter):
    """
    Return a dictionary of terms and weights of all terms of a set of
    documents, based on the frequency of terms in the selected set (docids).
    """
    normalized_weigths = {}
    population = [d.weight for d in docs]
    mean = sum(population)/len(population)
    variance = sum([(p-mean)*(p-mean) for p in population])/len(population)
    standard_deviation = math.sqrt(variance)
    for d in docs:
        if standard_deviation>1:
            # values between [0-1] would cause the opposite effect
            normalized_weigths[d.docid] = d.weight/standard_deviation
        else:
            normalized_weigths[d.docid] = d.weight
    return tfidf_weighting(index,docs,content_filter,normalized_weigths)

class FilteredXapianIndex(xapian.WritableDatabase):
    """
    Filtered Xapian Index
    """
    def __init__(self,terms,index_path,path):
        xapian.WritableDatabase.__init__(self,path,
                                         xapian.DB_CREATE_OR_OVERWRITE)
        index = xapian.Database(index_path)
        for docid in range(1,index.get_lastdocid()+1):
            try:
                doc = index.get_document(docid)
                docterms = [term.term for term in doc.termlist()]
                tagged = False
                for t in terms:
                    if t in docterms:
                        tagged = True
                if tagged:
                    self.add_document(doc)
                    logging.info("Added doc %d." % docid)
                else:
                    logging.info("Discarded doc %d." % docid)
            except:
                logging.info("Doc %d not found in axi." % docid)
        logging.info("Filter: %s" % terms)
        logging.info("Index size: %d" % index.get_doccount())
        logging.info("Filtered Index size: %d (lastdocid: %d)." %
                     (self.get_doccount(), self.get_lastdocid()))

    def __str__(self):
        return print_index(self)

class SampleAptXapianIndex(xapian.WritableDatabase):
    """
    Sample data source for packages information, generated from a list of
    packages.
    """
    def __init__(self,pkgs_list,axi,path):
        xapian.WritableDatabase.__init__(self,path,
                                         xapian.DB_CREATE_OR_OVERWRITE)
        sample = axi_search_pkgs(axi,pkgs_list)
        for package in sample:
            doc_id = self.add_document(axi.get_document(package.docid))

    def __str__(self):
        return print_index(self)

class DebianPackage():
    """
    Class to load package information.
    """
    def __init__(self,pkg_name):
        self.name = pkg_name

    def load_details_from_apt(self):
        pkg_version = apt.Cache()[self.name].candidate

        self.maintainer = pkg_version.record['Maintainer']
        self.version = pkg_version.version
        self.summary = pkg_version.summary
        self.description = self.format_description(pkg_version.description)
        self.summary = pkg_version.section
        if pkg_version.record.has_key('Homepage'):
            self.homepage = pkg_version.record['Homepage']
        if pkg_version.record.has_key('Tag'):
            self.tags = self.debtags_str_to_dict(pkg_version.record['Tag'])
        if pkg_version.record.has_key('Depends'):
            self.depends = pkg_version.record['Depends']
        if pkg_version.record.has_key('Pre-Depends'):
            self.predepends = pkg_version.record['Pre-Depends']
        if pkg_version.record.has_key('Recommends'):
            self.recommends = pkg_version.record['Recommends']
        if pkg_version.record.has_key('Suggests'):
            self.suggests = pkg_version.record['Suggests']
        if pkg_version.record.has_key('Breaks'):
            self.breaks = pkg_version.record['Breaks']
        if pkg_version.record.has_key('Conflicts'):
            self.conflicts = pkg_version.record['Conflicts']
        if pkg_version.record.has_key('Replaces'):
            self.conflicts = pkg_version.record['Replaces']
        if pkg_version.record.has_key('Provides'):
            self.provides = pkg_version.record['Provides']

    def load_details_from_dde(self,dde_server,dde_port):
        json_data = json.load(urllib.urlopen("http://%s:%d/q/udd/packages/all/%s?t=json"
                                             % (dde_server,dde_port,self.name)))

        self.maintainer = json_data['r']['maintainer']
        self.version = json_data['r']['version']
        self.summary = json_data['r']['description']
        self.description = self.format_description(json_data['r']['long_description'])
        self.section = json_data['r']['section']
        if json_data['r']['homepage']:
            self.conflicts = json_data['r']['homepage']
        if json_data['r']['tag']:
            self.tags = self.debtags_list_to_dict(json_data['r']['tag'])
        if json_data['r']['depends']:
            self.depends = json_data['r']['depends']
        if json_data['r']['pre_depends']:
            self.conflicts = json_data['r']['pre_depends']
        if json_data['r']['recommends']:
            self.conflicts = json_data['r']['recommends']
        if json_data['r']['suggests']:
            self.conflicts = json_data['r']['suggests']
        if json_data['r']['conflicts']:
            self.conflicts = json_data['r']['conflicts']
        if json_data['r']['replaces']:
            self.conflicts = json_data['r']['replaces']
        if json_data['r']['provides']:
            self.conflicts = json_data['r']['provides']
        self.popcon_insts = json_data['r']['popcon']['insts']

    def format_description(self,description):
        return description.replace(' .\n','<br />').replace('\n','<br />')

    def debtags_str_to_dict(self, debtags_str):
        debtags_list = [tag.rstrip(",") for tag in debtags_str.split()]
        return self.debtags_list_to_dict(debtags_list)

    def debtags_list_to_dict(self, debtags_list):
        """ input:  ['use::editing',
        	         'works-with-format::gif',
                     'works-with-format::jpg',
                     'works-with-format::pdf']
            output: {'use': [editing],
                     'works-with-format': ['gif', 'jpg', 'pdf']'}
        """
        debtags = {}
        subtags = []
        for tag in debtags_list:
            match = re.search(r'^(.*)::(.*)$', tag)
            if not match:
                logging.info("Could not parse debtags format from tag: %s", tag)
            facet, subtag = match.groups()
            subtags.append(subtag)
            if facet not in debtags:
               debtags[facet] = subtags
            else:
               debtags[facet].append(subtag)
            subtags = []
        print "debtags_list",debtags
        return debtags

class PopconSubmission():
    def __init__(self,path,user_id=0,binary=1):
        self.packages = dict()
        self.path = path
        self.binary = binary
        self.load()
        if user_id:
            self.user_id = user_id

    def __str__(self):
        output = "\nPopularity-contest submission ID "+self.user_id
        for pkg, weight in self.packages.items():
            output += "\n "+pkg+": "+str(weight)
        return output

    def get_filtered(self,filter_list):
        filtered = {}
        for pkg in self.packages.keys():
            if pkg in filter_list:
                filtered[pkg] = self.packages[pkg]
        return filtered

    def load(self,binary=1):
    	"""
    	Parse a popcon submission, generating the names of the valid packages
        in the vote.
    	"""
        with open(self.path) as submission:
    	    for line in submission:
                if line.startswith("POPULARITY"):
                    self.user_id = line.split()[2].lstrip("ID:")
                    self.arch = line.split()[3].lstrip("ARCH:")
                elif not line.startswith("END-POPULARITY"):
                    data = line.rstrip('\n').split()
                    if len(data) > 2:
                        pkg = data[2]
                        if len(data) > 3:
                            exec_file = data[3]
                            # Binary weight
                            if self.binary:
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

class FilteredPopconXapianIndex(xapian.WritableDatabase):
    """
    Data source for popcon submissions defined as a xapian database.
    """
    def __init__(self,path,popcon_dir,axi_path,tags_filter):
        """
        Set initial attributes.
        """
        self.axi = xapian.Database(axi_path)
        self.path = os.path.expanduser(path)
        self.popcon_dir = os.path.expanduser(popcon_dir)
        self.valid_pkgs = axi_get_pkgs(self.axi)
        logging.debug("Considering %d valid packages" % len(self.valid_pkgs))
        with open(tags_filter) as valid_tags:
            self.valid_tags = [line.strip() for line in valid_tags
                               if not line.startswith("#")]
        logging.debug("Considering %d valid tags" % len(self.valid_tags))
        if not os.path.exists(self.popcon_dir):
            os.makedirs(self.popcon_dir)
        if not os.listdir(self.popcon_dir):
            logging.critical("Popcon dir seems to be empty.")
            raise Error

        # set up directory
        shutil.rmtree(self.path,1)
        os.makedirs(self.path)
        try:
            logging.info("Indexing popcon submissions from \'%s\'" %
                         self.popcon_dir)
            logging.info("Creating new xapian index at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self,self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError as e:
            logging.critical("Could not create popcon xapian index.")
            logging.critical(str(e))
            raise Error

        # build new index
        doc_count = 0
        for root, dirs, files in os.walk(self.popcon_dir):
            for popcon_file in files:
                submission = PopconSubmission(os.path.join(root, popcon_file))
                doc = xapian.Document()
                submission_pkgs = submission.get_filtered(self.valid_pkgs)
                if len(submission_pkgs) < 10:
                    logging.debug("Low profile popcon submission \'%s\' (%d)" %
                                  (submission.user_id,len(submission_pkgs)))
                else:
                    doc.set_data(submission.user_id)
                    doc.add_term("ID"+submission.user_id)
                    doc.add_term("ARCH"+submission.arch)
                    logging.debug("Parsing popcon submission \'%s\'" %
                                  submission.user_id)
                    for pkg,freq in submission_pkgs.items():
                        tags = axi_search_pkg_tags(self.axi,pkg)
                        # if the package was found in axi
                        if tags:
                            doc.add_term("XP"+pkg,freq)
                            # if the package has tags associated with it
                            if not tags == "notags":
                                for tag in tags:
                                    if tag.lstrip("XT") in self.valid_tags:
                                        doc.add_term(tag,freq)
                    doc_id = self.add_document(doc)
                    doc_count += 1
                    logging.debug("Popcon Xapian: Indexing doc %d" % doc_id)
            # python garbage collector
        	gc.collect()
        # flush to disk database changes
        try:
            self.commit()
        except:
            self.flush() # deprecated function, used for compatibility with old lib version

# Deprecated class, must be reviewed
class PopconXapianIndex(xapian.WritableDatabase):
    """
    Data source for popcon submissions defined as a singleton xapian database.
    """
    def __init__(self,cfg):
        """
        Set initial attributes.
        """
        self.axi = xapian.Database(cfg.axi)
        self.path = os.path.expanduser(cfg.popcon_index)
        self.source_dir = os.path.expanduser(cfg.popcon_dir)
        self.max_popcon = cfg.max_popcon
        self.valid_pkgs = []
        # file format for filter: one package name per line
        with open(cfg.pkgs_filter) as valid_pkgs:
            self.valid_pkgs = [line.strip() for line in valid_pkgs
                               if not line.startswith("#")]
        logging.debug("Considering %d valid packages" % len(self.valid_pkgs))
        with open(os.path.join(cfg.filters_dir,"debtags")) as valid_tags:
            self.valid_tags = [line.strip() for line in valid_tags
                               if not line.startswith("#")]
        logging.debug("Considering %d valid tags" % len(self.valid_tags))
        if not cfg.index_mode == "old" or not self.load_index():
            if not os.path.exists(cfg.popcon_dir):
                os.makedirs(cfg.popcon_dir)
            if not os.listdir(cfg.popcon_dir):
                logging.critical("Popcon dir seems to be empty.")
                raise Error
            if cfg.index_mode == "reindex" or cfg.index_mode == "old":
                self.source_dir = os.path.expanduser(cfg.popcon_dir)
                logging.debug(self.source_dir)
            else:
                self.source_dir = os.path.expanduser(cfg.clusters_dir)
                if not os.path.exists(cfg.clusters_dir):
                    os.makedirs(cfg.clusters_dir)
                if not os.listdir(cfg.clusters_dir) or \
                    cfg.index_mode == "recluster":
                    shutil.rmtree(cfg.clusters_dir,1)
                    os.makedirs(cfg.clusters_dir)
                    logging.info("Clustering popcon submissions from \'%s\'"
                                 % cfg.popcon_dir)
                    logging.info("Clusters will be placed at \'%s\'"
                                 % cfg.clusters_dir)
                    distance = JaccardDistance()
                    data = self.get_submissions(cfg.popcon_dir)
                    logging.debug(type(data))
                    self.cluster_dispersion = \
                        self.kmedoids_clustering(data, cfg.clusters_dir,
                                                 distance, cfg.k_medoids,
                                                 cfg.max_popcon)
                    logging.info("Clusters dispersion: %.2f",
                                 self.cluster_dispersion)
                else:
                    logging.info("Using clusters from \'%s\'" %
                                 cfg.clusters_dir)
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
            return 1
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
        except xapian.DatabaseError as e:
            logging.critical("Could not create popcon xapian index.")
            logging.critical(str(e))
            raise Error

        doc_count = 0
        for root, dirs, files in os.walk(self.source_dir):
            if doc_count == self.max_popcon:
                break
            for popcon_file in files:
                if doc_count == self.max_popcon:
                    break
                submission = PopconSubmission(os.path.join(root, popcon_file))
                doc = xapian.Document()
                submission_pkgs = submission.get_filtered(self.valid_pkgs)
                if len(submission_pkgs) < 10:
                    logging.debug("Low profile popcon submission \'%s\' (%d)" %
                                  (submission.user_id,len(submission_pkgs)))
                else:
                    doc.set_data(submission.user_id)
                    logging.debug("Parsing popcon submission \'%s\'" %
                                  submission.user_id)
                    for pkg,freq in submission_pkgs.items():
                        tags = axi_search_pkg_tags(self.axi,pkg)
                        # if the package was foung in axi
                        if tags:
                            doc.add_term("XP"+pkg,freq)
                            # if the package has tags associated with it
                            if not tags == "notags":
                                for tag in tags:
                                    if tag.lstrip("XT") in self.valid_tags:
                                        doc.add_term(tag,freq)
                    doc_id = self.add_document(doc)
                    doc_count += 1
                    logging.debug("Popcon Xapian: Indexing doc %d" % doc_id)
            # python garbage collector
        	gc.collect()
        # flush to disk database changes
        try:
            self.commit()
        except:
            self.flush() # deprecated function, used for compatibility with old lib version

    def get_submissions(self,submissions_dir):
        """
        Get popcon submissions from popcon_dir
        """
        submissions = []
        for root, dirs, files in os.walk(submissions_dir):
            for popcon_file in files:
                logging.debug("Parsing submission %s" % popcon_file)
                submission = PopconSubmission(os.path.join(root, popcon_file))
                submissions.append(submission)
        return submissions

    def kmedoids_clustering(self,data,clusters_dir,distance,k_medoids,max_popcon):
        clusters = KMedoidsClustering(data,lambda x,y:
                                           distance(x.packages.keys(),
                                                    y.packages.keys()),max_popcon)
        medoids,dispersion = clusters.getMedoids(k_medoids)
        for submission in medoids:
            logging.debug("Copying submission %s" % submission.user_id)
            shutil.copyfile(submission.path,os.path.join(clusters_dir,
                                                         submission.user_id))
        return dispersion

class KMedoidsClustering(cluster.KMeansClustering):

    def __init__(self,data,distance,max_data):
        if len(data)<max_data:
            data_sample = data
        else:
            data_sample = random.sample(data,max_data)
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
            logging.debug("totalDistance[%d]=%f" % (i,totalDistance))
            if totalDistance < medoidDistance:
                medoidDistance = totalDistance
                medoid = i
            logging.debug("medoidDistance: %f" % medoidDistance)
        logging.debug("Cluster medoid: [%d] %s" % (medoid,
                                                   cluster[medoid].user_id))
        return (cluster[medoid],medoidDistance)

    def assign_item(self, item, origin):
        """
        Assigns an item from a given cluster to the closest located cluster
        """
        closest_cluster = origin
        for cluster in self._KMeansClustering__clusters:
            if self.distance(item,self.getMedoid(cluster)[0]) < \
                self.distance(item,self.getMedoid(closest_cluster)[0]):
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
        #medoids_distances = [self.getMedoid(cluster) for cluster in self.getclusters(n)]
        medoids_distances = []
        logging.debug("initial length %s" % self._KMeansClustering__initial_length)
        logging.debug("n %d" % n)
        for cluster in self.getclusters(n):
            type(cluster)
            print cluster
            medoids_distances.append(self.getMedoid(cluster))
            print medoids_distances
        medoids = [m[0] for m in medoids_distances]
        dispersion = sum([m[1] for m in medoids_distances])
        logging.info("Clustering completed and the following medoids were found: %s" % [c.user_id for c in medoids])
        return medoids,dispersion
