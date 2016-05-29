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

import xapian
import logging
import random
import operator
import math
import commands

from apprecommender.utils import print_progress_bar
from apprecommender.data_classification import time_weight
from apprecommender.error import Error


def axi_get_pkgs(axi):
    pkgs_names = []
    pkgs_terms = {}

    for docid in range(1, axi.get_lastdocid() + 1):
        try:
            doc = axi.get_document(docid)
        except:
            continue

        docterms_XP, docterms_XT = [], []
        for terms in doc.termlist():
            if terms.term.startswith('XP'):
                docterms_XP.append(terms.term)
            elif terms.term.startswith('XT'):
                docterms_XT.append(terms.term)

        pkg_name = docterms_XP[0].lstrip('XP')
        pkgs_names.append(pkg_name)

        pkgs_terms[pkg_name] = docterms_XT

    return pkgs_names, pkgs_terms


def axi_search_pkgs(axi, pkgs_list):
    terms = ["XP" + item for item in pkgs_list]
    query = xapian.Query(xapian.Query.OP_OR, terms)
    enquire = xapian.Enquire(axi)
    enquire.set_query(query)
    mset = enquire.get_mset(0, axi.get_doccount())
    return mset


def axi_search_pkg_tags(axi, pkg):
    enquire = xapian.Enquire(axi)
    enquire.set_query(xapian.Query("XP" + pkg))
    matches = enquire.get_mset(0, 1)
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
        output += term.term + "\n"
        output += str([index.get_document(posting.docid).get_data()
                       for posting in index.postlist(term.term)])
        output += "\n---"
    return output


def get_user_installed_pkgs():
    dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')

    packages = [pkg.split('\t')[0] for pkg in dpkg_output.splitlines()
                if 'deinstall' not in pkg.split('\t')[-1]]

    packages = set(packages)

    return packages


def get_all_terms(index, docs, content_filter, normalized_weights):
    # Store all terms in one single document

    terms_packages = {}
    terms_doc = xapian.Document()

    for d in docs:

        package = d.document.get_data()

        for term in index.get_document(d.docid).termlist():

            if content_filter(term.term):
                if normalized_weights:
                    terms_doc.add_term(term.term,
                                       int(math.ceil(
                                           normalized_weights[d.docid])))
                else:
                    terms_doc.add_term(term.term)

            if term.term.startswith('XP'):
                continue
            elif term.term in terms_packages:
                terms_packages[term.term].append(package)
            else:
                terms_packages[term.term] = [package]

    return (terms_doc, terms_packages)


def get_tfidf_terms_weights(terms_doc, index, terms_package, time_context=0):

    # Compute sublinear tfidf for each term
    weights = {}
    for term in terms_doc.termlist():
        try:
            # Even if it shouldn't raise error...
            # math.log: ValueError: math domain error
            tf = 1 + math.log(term.wdf)
            idf = math.log(index.get_doccount() /
                           float(index.get_termfreq(term.term)))

            tfidf = tf * idf
            weights[term.term] = tfidf

            if time_context:
                weight = time_weight(term.term,
                                     terms_package[term.term])
                weights[term.term] *= weight
        except:
            pass

    # print_best_weight_terms(terms_package)

    return weights


def tfidf_weighting(index, docs, content_filter, normalized_weights=0,
                    time_context=0):
    """
    Return a dictionary of terms and weights of all terms of a set of
    documents, based on the frequency of terms in the selected set (docids).
    """

    terms_doc, terms_packages = get_all_terms(index, docs, content_filter,
                                              normalized_weights)
    weights = get_tfidf_terms_weights(terms_doc, index, terms_packages,
                                      time_context)

    sorted_weights = list(reversed(sorted(weights.items(),
                                          key=operator.itemgetter(1))))
    return sorted_weights


def tfidf_plus(index, docs, content_filter, time_context=0):
    """
    Return a dictionary of terms and weights of all terms of a set of
    documents, based on the frequency of terms in the selected set (docids).
    """
    normalized_weigths = {}
    population = [d.weight for d in docs]
    mean = sum(population) / len(population)
    variance = sum([(p - mean) * (p - mean)
                   for p in population]) / len(population)
    standard_deviation = math.sqrt(variance)
    for d in docs:
        if standard_deviation > 1:
            # values between [0-1] would cause the opposite effect
            normalized_weigths[d.docid] = d.weight / standard_deviation
        else:
            normalized_weigths[d.docid] = d.weight
    return tfidf_weighting(index, docs, content_filter, normalized_weigths,
                           time_context)


def split_pkg_data(user_pkg, partition_size):
    round_partition = {}

    for i in range(partition_size):

        if len(user_pkg) > 0:
            random_key = random.choice(user_pkg.keys())
        else:
            logging.critical("Empty user_pkg.")
            raise Error

        round_partition[random_key] = user_pkg.pop(random_key)

    return round_partition


class FilteredXapianIndex(xapian.WritableDatabase):

    """
    Filtered Xapian Index
    """

    def __init__(self, terms, index_path, path):
        xapian.WritableDatabase.__init__(self, path,
                                         xapian.DB_CREATE_OR_OVERWRITE)
        index = xapian.Database(index_path)
        for docid in range(1, index.get_lastdocid() + 1):
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

    def __init__(self, pkgs_list, axi, path):
        xapian.WritableDatabase.__init__(self, path,
                                         xapian.DB_CREATE_OR_OVERWRITE)
        self.sample = axi_search_pkgs(axi, pkgs_list)
        len_sample = len(self.sample)

        for index, package in enumerate(self.sample):
            self.doc_id = self.add_document(axi.get_document(package.docid))
            print_progress_bar(index + 1, len_sample)

    def __str__(self):
        return print_index(self)


class PopconSubmission():

    def __init__(self, path, user_id=0, binary=1):
        self.packages = dict()
        self.path = path
        self.binary = binary
        self.load()
        if user_id:
            self.user_id = user_id

    def __str__(self):
        output = "\nPopularity-contest submission ID " + self.user_id
        for pkg, weight in self.packages.items():
            output += "\n " + pkg + ": " + str(weight)
        return output

    def get_filtered(self, filter_list):
        filtered = {}
        for pkg in self.packages.keys():
            if pkg in filter_list:
                filtered[pkg] = self.packages[pkg]
        return filtered

    def load(self, binary=1):
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


class KnnXapianIndex(xapian.WritableDatabase):

    def __init__(self, path, submissions, axi_path, tags_filter):
        self.axi = xapian.Database(axi_path)
        self.path = os.path.expanduser(path)
        self.submissions = submissions
        self.valid_pkgs, self.pkgs_terms = axi_get_pkgs(self.axi)
        logging.debug("Considering %d valid packages" % len(self.valid_pkgs))
        if len(self.submissions) == 0:
            logging.critical("Knn submissions can't be empty")
            raise Error

        # set up directory
        shutil.rmtree(self.path, 1)
        os.makedirs(self.path)
        try:
            logging.info("Creating new xapian index at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self, self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError as e:
            logging.critical("Could not create popcon xapian index.")
            logging.critical(str(e))
            raise Error

        # build new index
        doc_count = 0
        len_submissions = len(submissions)
        for submission in submissions:
            doc = xapian.Document()
            submission_pkgs = [pkg for pkg in submission
                               if pkg in self.valid_pkgs]

            for pkg_name in submission_pkgs:
                pkg_terms = self.pkgs_terms[pkg_name]
                doc.add_term('XP' + pkg_name)
                for term in pkg_terms:
                    doc.add_term(term)

            self.add_document(doc)
            doc_count += 1
            gc.collect()
            print_progress(doc_count, len_submissions)
        try:
            # flush to disk database changes
            self.commit()
        except:
            # deprecated function, used for compatibility with old lib version
            self.flush()
