#!/usr/bin/env python
"""
    strategy - python module for classes and methods related to recommendation
               strategies.
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
import xapian
import recommender
import data
import logging
import pickle
import numpy as np

from os import path
from error import Error
from config import Config
from bayes_matrix import BayesMatrix
from bin.pkg_classification import MachineLearningData

XAPIAN_DATABASE_PATH = path.expanduser('~/.app-recommender/axi_desktopapps/')
USER_DATA_DIR = Config().user_data_dir
PKGS_CLASSIFICATIONS_INDICES = (USER_DATA_DIR +
                                'pkgs_classifications_indices.txt')
MACHINE_LEARNING_TERMS = USER_DATA_DIR + 'machine_learning_terms.txt'
MACHINE_LEARNING_DEBTAGS = USER_DATA_DIR + 'machine_learning_debtags.txt'
MACHINE_LEARNING_TRAINING = USER_DATA_DIR + 'machine_learning_training.txt'


class PkgMatchDecider(xapian.MatchDecider):

    """
    Extend xapian.MatchDecider to not consider installed packages.
    """

    def __init__(self, pkgs_list):
        """
        Set initial parameters.
        """
        xapian.MatchDecider.__init__(self)
        self.pkgs_list = pkgs_list

    def __call__(self, doc):
        """
        True if the package is not already installed.
        """
        pkg = doc.get_data()
        is_new = pkg not in self.pkgs_list
        if "kde" in pkg:
            return is_new and "kde" in self.pkgs_list
        if "gnome" in pkg:
            return is_new and "gnome" in self.pkgs_list
        return is_new


class PkgExpandDecider(xapian.ExpandDecider):

    """
    Extend xapian.ExpandDecider to consider packages only.
    """

    def __init__(self, pkgs_list):
        """
        Set initial parameters.
        """
        xapian.ExpandDecider.__init__(self)
        self.pkgs_list = pkgs_list

    def __call__(self, term):
        """
        True if the term is a package.
        """
        pkg = term.lstrip("XP")
        is_new_pkg = pkg not in self.pkgs_list and term.startswith("XP")
        if "kde" in pkg:
            return is_new_pkg and "kde" in self.pkgs_list
        if "gnome" in pkg:
            return is_new_pkg and "gnome" in self.pkgs_list
        return is_new_pkg


class TagExpandDecider(xapian.ExpandDecider):

    """
    Extend xapian.ExpandDecider to consider tags only.
    """

    def __call__(self, term):
        """
        True if the term is a package tag.
        """
        return term.startswith("XT")


class RecommendationStrategy:

    """
    Base class for recommendation strategies.
    """

    def run(self, rec, user, recommendation_size):
        raise NotImplementedError


class ContentBased(RecommendationStrategy):

    """
    Content-based recommendation strategy based on Apt-xapian-index.
    """

    def __init__(self, content, profile_size):
        self.description = "Content-based"
        self.content = content
        self.profile_size = profile_size

    def get_sugestion_from_profile(self, rec, user, profile,
                                   recommendation_size):
        query = xapian.Query(xapian.Query.OP_OR, profile)
        enquire = xapian.Enquire(rec.items_repository)
        enquire.set_weighting_scheme(rec.weight)
        enquire.set_query(query)
        # Retrieve matching packages
        try:
            mset = enquire.get_mset(0, recommendation_size, None,
                                    PkgMatchDecider(user.items()))
        except xapian.DatabaseError as error:
            logging.critical("Content-based strategy: " + error.get_msg())

        # Compose result dictionary
        item_score = {}
        ranking = []
        for m in mset:
            item_score[m.document.get_data()] = m.weight
            ranking.append(m.document.get_data())

        result = recommender.RecommendationResult(item_score, ranking)
        return result

    def run(self, rec, user, rec_size):
        """
        Perform recommendation strategy.
        """
        logging.debug("Composing user profile...")
        profile = user.content_profile(rec.items_repository, self.content,
                                       self.profile_size, rec.valid_tags)
        logging.debug(profile)
        result = self.get_sugestion_from_profile(rec, user, profile, rec_size)
        return result


class Collaborative(RecommendationStrategy):

    """
    Colaborative recommendation strategy.
    """

    def get_user_profile(self, user, rec):
        logging.debug("Composing user profile...")
        profile = ["XP" + package for package in
                   user.filter_pkg_profile(rec.valid_pkgs)]
        logging.debug(profile)
        return profile

    def get_enquire(self, rec):
        enquire = xapian.Enquire(rec.users_repository)
        enquire.set_weighting_scheme(rec.weight)
        return enquire

    # def get_rset_from_profile(self, profile):
    # Create document to represent user profile and mark it as relevant
    #    return rset

    def get_neighborhood(self, user, rec):
        profile = self.get_user_profile(user, rec)
        # query = xapian.Query(xapian.Query.OP_OR,profile)
        query = xapian.Query(xapian.Query.OP_ELITE_SET, profile)
        enquire = self.get_enquire(rec)
        enquire.set_query(query)
        # Retrieve matching users
        try:
            mset = enquire.get_mset(0, self.neighbours)
        except xapian.DatabaseError as error:
            error_msg = "Could not compose user neighborhood.\n "
            logging.critical(error_msg + error.get_msg())
            raise Error
        return mset

    def get_neighborhood_rset(self, user, rec):
        mset = self.get_neighborhood(user, rec)
        rset = xapian.RSet()
        for m in mset:
            rset.add_document(m.document.get_docid())
        return rset

    def get_result_from_eset(self, eset):
        # compose result dictionary
        item_score = {}
        ranking = []
        for e in eset:
            package = e.term.lstrip("XP")
            item_score[package] = e.weight
            ranking.append(package)
        return recommender.RecommendationResult(item_score, ranking)


class Knn(Collaborative):

    """
    KNN based packages tf-idf weights.
    """

    def __init__(self, k):
        self.description = "Knn"
        self.neighbours = k

    def run(self, rec, user, recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighborhood = self.get_neighborhood(user, rec)
        weights = data.tfidf_weighting(rec.users_repository, neighborhood,
                                       PkgExpandDecider(user.items()))
        item_score = {}
        ranking = []
        for pkg in weights[:recommendation_size]:
            package = pkg[0].lstrip("XP")
            item_score[package] = pkg[1]
            ranking.append(package)
        result = recommender.RecommendationResult(item_score, ranking)
        return result


class KnnPlus(Collaborative):

    """
    KNN based packages tf-idf weights.
    """

    def __init__(self, k):
        self.description = "Knn plus"
        self.neighbours = k

    def run(self, rec, user, recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighborhood = self.get_neighborhood(user, rec)
        weights = data.tfidf_plus(rec.users_repository, neighborhood,
                                  PkgExpandDecider(user.items()))
        item_score = {}
        ranking = []
        for pkg in weights[:recommendation_size]:
            package = pkg[0].lstrip("XP")
            item_score[package] = pkg[1]
            ranking.append(package)
        result = recommender.RecommendationResult(item_score, ranking)
        return result


class KnnEset(Collaborative):

    """
    KNN based on query expansion.
    """

    def __init__(self, k):
        self.description = "KnnEset"
        self.neighbours = k

    def run(self, rec, user, recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighbors_rset = self.get_neighborhood_rset(user, rec)
        enquire = self.get_enquire(rec)
        # Retrieve new packages based on neighborhood profile expansion
        eset = enquire.get_eset(recommendation_size, neighbors_rset,
                                PkgExpandDecider(user.items()))
        result = self.get_result_from_eset(eset)
        return result


class CollaborativeEset(Collaborative):

    """
    Colaborative strategy based on query expansion.
    """

    def __init__(self):
        self.description = "Collaborative-Eset"

    def run(self, rec, user, recommendation_size):
        """
        Perform recommendation strategy.
        """
        temp_index = xapian.WritableDatabase("/tmp/Database",
                                             xapian.DB_CREATE_OR_OVERWRITE)
        profile = self.get_user_profile(user, rec)
        doc = xapian.Document()
        for pkg in profile:
            doc.add_term(pkg)
        doc.add_term("TO_BE_DELETED")
        docid = temp_index.add_document(doc)
        temp_index.add_database(rec.users_repository)
        rset = xapian.RSet()
        rset.add_document(docid)
        # rset = self.get_rset_from_profile(profile)
        enquire = xapian.Enquire(temp_index)
        enquire.set_weighting_scheme(rec.weight)
        eset = enquire.get_eset(recommendation_size, rset,
                                PkgExpandDecider(user.items()))
        result = self.get_result_from_eset(eset)
        return result


class KnnContent(Collaborative):

    """
    Hybrid "Colaborative through content" recommendation strategy.
    """

    def __init__(self, k):
        self.description = "Knn-Content"
        self.neighbours = k

    def run(self, rec, user, recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighborhood = self.get_neighborhood(user, rec)
        weights = data.tfidf_weighting(rec.users_repository, neighborhood,
                                       PkgExpandDecider(user.items()))
        profile = [w[0] for w in weights][:rec.cfg.profile_size]

        result = ContentBased("tag", rec.cfg.profile_size)
        result = result.get_sugestion_from_profile(rec, user, profile,
                                                   recommendation_size)
        return result


class KnnContentEset(Collaborative):

    """
    Hybrid "Colaborative through content" recommendation strategy.
    """

    def __init__(self, k):
        self.description = "Knn-Content-Eset"
        self.neighbours = k

    def run(self, rec, user, recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighbors_rset = self.get_neighborhood_rset(user, rec)
        enquire = self.get_enquire(rec)
        # Retrieve relevant tags based on neighborhood profile expansion
        eset = enquire.get_eset(rec.cfg.profile_size, neighbors_rset,
                                TagExpandDecider())
        profile = [e.term for e in eset]
        result = ContentBased("tag", rec.cfg.profile_size)
        result = result.get_sugestion_from_profile(rec, user, profile,
                                                   recommendation_size)
        return result


class Demographic(RecommendationStrategy):

    """
    Hybrid rotation strategy based on demographic data.
    """

    def __init__(self, strategy_str):
        self.description = "Demographic"
        self.strategy_str = strategy_str.lstrip("demo_")

    def run(self, rec, user, recommendation_size):
        """
        Perform recommendation strategy.
        """
        filters_dir = rec.cfg.filters_dir
        program_dir = os.path.join(filters_dir, "programs")
        desktop_dir = os.path.join(filters_dir, "desktopapps")

        program_profile = user.filter_pkg_profile(program_dir)
        desktop_profile = user.filter_pkg_profile(desktop_dir)
        if len(desktop_profile) > 10 or (len(desktop_profile) >
                                         len(program_profile) / 2):
            rec.set_strategy(self.strategy_str)
            # Redefine repositories after configuring strategy
            rec.items_repository = rec.axi_desktopapps
            rec.valid_pkgs = rec.valid_desktopapps
            if "col" in self.strategy_str:
                rec.users_repository = rec.popcon_desktopapps
        return rec.get_recommendation(user, recommendation_size)


class MachineLearning(ContentBased):

    def __init__(self, content, profile_size):
        ContentBased.__init__(self, content, profile_size)
        self.description = "Machine-learning"
        self.content = content
        self.profile_size = profile_size

    def run(self, rec, user, rec_size):
        terms_name = []
        debtags_name = []
        with open(MACHINE_LEARNING_TERMS, 'rb') as text:
            terms_name = pickle.load(text)
        with open(MACHINE_LEARNING_DEBTAGS, 'rb') as text:
            debtags_name = pickle.load(text)

        profile = debtags_name + terms_name

        ml_data = MachineLearningData()
        bayes_matrix = BayesMatrix.load(MACHINE_LEARNING_TRAINING)

        axi = xapian.Database(XAPIAN_DATABASE_PATH)
        pkgs_classifications = {}

        pkgs = self.get_sugestion_from_profile(rec, user, profile, 200)
        pkgs = [pkg.split(':')[1][1:]
                for pkg in str(pkgs).splitlines()[1:]]

        for pkg in pkgs:
            pkg_terms = ml_data.get_pkg_terms(axi, pkg)
            pkg_debtags = ml_data.get_pkg_debtags(axi, pkg)
            debtags_attributes = ml_data.create_row_table_list(debtags_name,
                                                               pkg_debtags)
            terms_attributes = ml_data.create_row_table_list(terms_name,
                                                             pkg_terms)
            attribute_vector = terms_attributes + debtags_attributes

            attribute_vector = np.matrix(attribute_vector)

            classification = bayes_matrix.get_classification(attribute_vector)
            pkgs_classifications[pkg] = classification

        print '=' * 80
        print pkgs_classifications
        print '=' * 80
        return pkgs
