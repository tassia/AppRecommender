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

import apt
import data
import logging
import operator
import os
import pickle
import re
import recommender
import xapian

import numpy as np

from abc import ABCMeta, abstractmethod
from os import path
from nltk.corpus import stopwords

from error import Error
from config import Config
from ml.bag_of_words import BagOfWords
from ml.bayes_matrix import BayesMatrix
from ml.data import MachineLearningData

XAPIAN_DATABASE_PATH = path.expanduser('~/.app-recommender/axi_desktopapps/')
USER_DATA_DIR = Config().user_data_dir
PKGS_CLASSIFICATIONS_INDICES = (USER_DATA_DIR +
                                'pkgs_classifications_indices.txt')


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
        True if the package is not already installed and is not a lib or a doc.
        """
        pkg = doc.get_data()
        is_new = pkg not in self.pkgs_list
        is_new = is_new and ':' not in pkg

        if "kde" in pkg:
            return is_new and "kde" in self.pkgs_list
        if "gnome" in pkg:
            return is_new and "gnome" in self.pkgs_list

        if re.match(r'^lib.*', pkg) or re.match(r'.*doc$', pkg):
            return False

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


class RecommendationStrategy(object):

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
                                    PkgMatchDecider(user.installed_pkgs))
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

    __metaclass__ = ABCMeta

    def __init__(self, content, profile_size, suggestion_size=200):
        ContentBased.__init__(self, content, profile_size)
        self.content = content
        self.description = 'Machine-learning'
        self.profile_size = profile_size
        self.suggestion_size = suggestion_size
        self.cache = apt.Cache()
        self.stop_words = set(stopwords.words('english'))
        self.ml_data = MachineLearningData()
        self.axi = xapian.Database(XAPIAN_DATABASE_PATH)

    def display_recommended_terms(self, terms_name, debtags_name, item_score,
                                  rec_size):
        sorted_result = sorted(item_score.items(), key=operator.itemgetter(1))
        sorted_result = list(reversed(sorted_result))
        sorted_result = [pkg[0] for pkg in sorted_result][0:rec_size]
        sorted_result = list(reversed(sorted_result))

        for pkg in sorted_result:
            pkg_terms = self.ml_data.get_pkg_terms(self.cache, pkg,
                                                   self.stop_words)
            pkg_debtags = self.ml_data.get_pkg_debtags(self.axi, pkg)

            terms_match = []
            for term in pkg_terms:
                if term in terms_name:
                    terms_match.append(term)

            debtags_match = []
            for debtag in pkg_debtags:
                if debtag in debtags_name:
                    debtags_match.append(debtag)

            print "\n\n="
            print "{0}".format(pkg)
            print "debtags:"
            print debtags_match
            print "-"
            print "terms:"
            print terms_match
            print "="

    def get_item_score(self, pkgs_score, pkgs_classifications):
        item_score = {}
        order = ['H', 'B', 'M', 'G', 'EX']
        order_values = [0, 1000, 2000, 3000, 4000]

        for pkg, classification in pkgs_classifications.iteritems():
            item_score[pkg] = order_values[order.index(classification)]
            item_score[pkg] += pkgs_score[pkg]

        return item_score

    def get_pkgs_and_scores(self, rec, user, profile):
        content_based = self.get_sugestion_from_profile(rec, user,
                                                        profile,
                                                        self.suggestion_size)
        pkgs, pkgs_score = [], {}
        for pkg_line in str(content_based).splitlines()[1:]:
            pkg = pkg_line.split(':')[1][1:]
            pkg_score = int(pkg_line.split(':')[0].strip())

            pkgs.append(pkg)
            pkgs_score[pkg] = self.suggestion_size - pkg_score

        return pkgs, pkgs_score

    def get_pkgs_classifications(self, pkgs, terms_name, debtags_name):
        ml_strategy = self.get_ml_strategy()
        pkgs_classifications = {}
        kwargs = {}

        kwargs['terms_name'] = terms_name
        kwargs['debtags_name'] = debtags_name
        kwargs['ml_strategy'] = ml_strategy

        for pkg in pkgs:

            if pkg not in self.cache:
                continue

            attribute_vector = self.prepare_pkg_data(
                pkg, **kwargs)

            classification = self.get_pkg_classification(
                ml_strategy, attribute_vector)
            pkgs_classifications[pkg] = classification

        return pkgs_classifications

    def get_profile(self, terms_name, debtags_name):
        profile = ['XT' + debtag for debtag in debtags_name]
        profile += terms_name

        return profile

    def load_terms_and_debtags(self):
        terms_name = []
        debtags_name = []

        terms_path = self.get_terms_path()
        debtags_path = self.get_debtags_path()

        with open(terms_path, 'rb') as terms:
            terms_name = pickle.load(terms)
        with open(debtags_path, 'rb') as debtags:
            debtags_name = pickle.load(debtags)

        return terms_name, debtags_name

    @abstractmethod
    def get_debtags_path(self):
        raise NotImplementedError("Method not implemented.")

    @abstractmethod
    def get_ml_strategy(self):
        raise NotImplementedError("Method not implemented.")

    @abstractmethod
    def get_pkg_classification(self, ml_strategy, attribute_vector):
        raise NotImplementedError("Method not implemented.")

    @abstractmethod
    def get_terms_path(self):
        raise NotImplementedError("Method not implemented.")

    @abstractmethod
    def prepare_pkg_data(self, pkg, **kwargs):
        raise NotImplementedError("Method not implemented.")

    def run(self, rec, user, rec_size):
        terms_name, debtags_name = self.load_terms_and_debtags()

        profile = self.get_profile(terms_name, debtags_name)
        pkgs, pkgs_score = self.get_pkgs_and_scores(rec, user, profile)

        pkgs_classifications = self.get_pkgs_classifications(pkgs, terms_name,
                                                             debtags_name)

        item_score = self.get_item_score(pkgs_score, pkgs_classifications)
        result = recommender.RecommendationResult(item_score, limit=rec_size)

        return result


class MachineLearningBVA(MachineLearning):

    def __init__(self, content, profile_size, suggestion_size=200):
        super(MachineLearningBVA, self).__init__(
            content, profile_size, suggestion_size)
        self.description = "Machine-learning-binary-vector-approach"

    def get_debtags_path(self):
        return MachineLearningData.MACHINE_LEARNING_DEBTAGS

    def get_ml_strategy(self):
        return BayesMatrix.load(
            MachineLearningData.MACHINE_LEARNING_TRAINING)

    def get_pkg_classification(self, ml_strategy, attribute_vector):
        return ml_strategy.get_classification(attribute_vector)

    def get_terms_path(self):
        return MachineLearningData.MACHINE_LEARNING_TERMS

    def prepare_pkg_data(self, pkg, **kwargs):

        terms_name = kwargs['terms_name']
        debtags_name = kwargs['debtags_name']

        pkg_terms = self.ml_data.get_pkg_terms(
            self.cache, pkg, self.stop_words)
        pkg_debtags = self.ml_data.get_pkg_debtags(self.axi, pkg)
        debtags_attributes = self.ml_data.create_row_table_list(
            debtags_name, pkg_debtags)
        terms_attributes = self.ml_data.create_row_table_list(
            terms_name, pkg_terms)
        attribute_vector = terms_attributes + debtags_attributes

        attribute_vector = np.matrix(attribute_vector)

        return attribute_vector


class MachineLearningBOW(MachineLearning):

    def __init__(self, content, profile_size, suggestion_size=200):
        super(MachineLearningBOW, self).__init__(
            content, profile_size, suggestion_size)
        self.description = "Machine-learning-bag-of-words"

    def get_debtags_path(self):
        return BagOfWords.BAG_OF_WORDS_DEBTAGS

    def get_ml_strategy(self):
        return BagOfWords.load(
            BagOfWords.BAG_OF_WORDS_MODEL)

    def get_pkg_classification(self, ml_strategy, attribute_vector):
        return ml_strategy.classify_pkg(attribute_vector)

    def get_terms_path(self):
        return BagOfWords.BAG_OF_WORDS_TERMS

    def prepare_pkg_data(self, pkg, **kwargs):
        ml_strategy = kwargs['ml_strategy']

        attribute_vector = ml_strategy.create_pkg_data(
            pkg, self.axi, self.cache, self.ml_data)
        return attribute_vector
