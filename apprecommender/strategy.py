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
import logging
import operator
import pickle
import re
import recommender
import xapian

import numpy as np

from abc import ABCMeta, abstractmethod
from os import path

from apprecommender.config import Config
from apprecommender.decider import PkgMatchDecider
from apprecommender.ml.bag_of_words import BagOfWords
from apprecommender.ml.bayes_matrix import BayesMatrix
from apprecommender.ml.data import MachineLearningData

XAPIAN_DATABASE_PATH = path.expanduser('~/.app-recommender/axi_desktopapps/')
USER_DATA_DIR = Config().user_data_dir
PKGS_CLASSIFICATIONS_INDICES = (USER_DATA_DIR +
                                'pkgs_classifications_indices.txt')


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
                                   recommendation_size, because=True):
        query = xapian.Query(xapian.Query.OP_OR, profile)
        enquire = xapian.Enquire(rec.items_repository)
        enquire.set_weighting_scheme(rec.weight)
        enquire.set_query(query)
        user_profile = None
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

        if because and Config().because:
            user_profile = user.pkg_profile

        result = recommender.RecommendationResult(
            item_score, ranking, user_profile=user_profile)
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


class MachineLearning(ContentBased):

    __metaclass__ = ABCMeta

    PKGS_CLASSIFICATIONS = None

    def __init__(self, content, profile_size, suggestion_size=200):
        ContentBased.__init__(self, content, profile_size)
        self.content = content
        self.description = 'Machine-learning'
        self.profile_size = profile_size
        self.suggestion_size = suggestion_size
        self.cache = apt.Cache()
        self.ml_data = MachineLearningData()
        self.axi = xapian.Database(XAPIAN_DATABASE_PATH)

    def display_recommended_terms(self, terms_name, debtags_name, item_score,
                                  rec_size):
        sorted_result = sorted(item_score.items(), key=operator.itemgetter(1))
        sorted_result = list(reversed(sorted_result))
        sorted_result = [pkg[0] for pkg in sorted_result][0:rec_size]
        sorted_result = list(reversed(sorted_result))

        for pkg in sorted_result:
            pkg_terms = self.ml_data.get_pkg_terms(self.cache, pkg)
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
        order = ['RU', 'U', 'NU']
        order_values = [0, 1000, 2000]

        for pkg, classification in pkgs_classifications.iteritems():
            item_score[pkg] = order_values[order.index(classification)]
            item_score[pkg] += pkgs_score[pkg]

        return item_score

    def get_pkgs_and_scores(self, rec, user):
        profile = user.content_profile(rec.items_repository, self.content,
                                       self.suggestion_size, rec.valid_tags)

        content_based = self.get_sugestion_from_profile(
            rec, user, profile, self.suggestion_size, because=False)
        pkgs, pkgs_score = [], {}

        for pkg_line in str(content_based).splitlines()[1:]:
            pkg = re.search(r'\d+:\s([\w-]+)', pkg_line)

            if not pkg.groups():
                continue

            pkg = pkg.groups()[0]
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

    @staticmethod
    def train(cls):
        if MachineLearning.PKGS_CLASSIFICATIONS is None:
            ml_data = MachineLearningData()
            labels = ['RU', 'U', 'NU']
            MachineLearning.PKGS_CLASSIFICATIONS = ml_data.create_data(labels)

        cls.run_train(MachineLearning.PKGS_CLASSIFICATIONS)

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

    @abstractmethod
    def run_train(cls, pkgs_classifications):
        raise NotImplementedError("Method not implemented.")

    def run(self, rec, user, rec_size):
        user_profile = None

        terms_name, debtags_name = self.load_terms_and_debtags()

        pkgs, pkgs_score = self.get_pkgs_and_scores(rec, user)

        pkgs_classifications = self.get_pkgs_classifications(pkgs, terms_name,
                                                             debtags_name)

        item_score = self.get_item_score(pkgs_score, pkgs_classifications)

        if Config().because:
            user_profile = user.pkg_profile

        return recommender.RecommendationResult(
            item_score, limit=rec_size, user_profile=user_profile)


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

        pkg_terms = self.ml_data.get_pkg_terms(self.cache, pkg)
        pkg_debtags = self.ml_data.get_pkg_debtags(self.axi, pkg)
        debtags_attributes = self.ml_data.create_row_table_list(
            debtags_name, pkg_debtags)
        terms_attributes = self.ml_data.create_row_table_list(
            terms_name, pkg_terms)
        attribute_vector = terms_attributes + debtags_attributes

        attribute_vector = np.matrix(attribute_vector)

        return attribute_vector

    @classmethod
    def run_train(cls, pkgs_classifications):
        all_matrix = (np.matrix(pkgs_classifications.values()))
        data_matrix = all_matrix[0:, 0:-1]
        classifications = all_matrix[0:, -1]
        order_of_classifications = ['NU', 'U', 'RU']

        bayes_matrix = BayesMatrix()
        bayes_matrix.training(data_matrix, classifications,
                              order_of_classifications)

        BayesMatrix.save(bayes_matrix,
                         MachineLearningData.MACHINE_LEARNING_TRAINING)


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

    @classmethod
    def run_train(cls, pkgs_classifications):
        bag_of_words = BagOfWords()
        pkgs_list = pkgs_classifications.keys()
        axi = xapian.Database(XAPIAN_DATABASE_PATH)

        bag_of_words.train_model(pkgs_list, axi)
        BagOfWords.save(bag_of_words, BagOfWords.BAG_OF_WORDS_MODEL)
