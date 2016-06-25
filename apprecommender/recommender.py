#!/usr/bin/env python
"""
    recommender - python module for classes related to recommenders.
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
import heapq
import logging
import operator
import os
import strategy
import xapian

from collections import namedtuple
from fuzzywuzzy import fuzz
from operator import attrgetter

from apprecommender.config import Config


class RecommendationResult:
    """
    Class designed to describe a recommendation result: items and scores.
    """
    def __init__(self, item_score, ranking=0, limit=0, user_profile=None):
        """
        Set initial parameters.
        """
        self.item_score = item_score
        self.size = len(item_score)
        self.limit = limit
        self.cache = apt.Cache()
        self.pkg_descriptions = {}

        if ranking:
            self.ranking = ranking

        if user_profile:
            self.fill_pkg_descriptions(user_profile)

    def fill_pkg_descriptions(self, user_profile):
        for pkg in user_profile:
            description = self.cache[pkg].candidate.description
            self.pkg_descriptions[pkg] = description.lower()

    def __str__(self):
        """
        String representation of the object.
        """
        result = self.get_prediction(self.limit)
        rec_str = '\n'
        index = 1

        for pkg, _ in result:
            summary = self.cache[pkg].candidate.summary
            description = self.cache[pkg].candidate.description
            rec_str += '{}: {} \t {}\n'.format(
                index, pkg.ljust(20), summary)

            if self.pkg_descriptions:
                because_pkgs = self.get_because(description.lower())
                rec_str += '   because you installed: \t {}\n\n'.format(
                    ', '.join(because_pkgs))

            index += 1

        return rec_str

    def get_because(self, rec_description):
        because = []
        PkgRatio = namedtuple('PkgRatio', ['pkg', 'ratio'])

        for pkg, description in self.pkg_descriptions.iteritems():
            ratio = fuzz.ratio(rec_description, description)
            because.append(PkgRatio(pkg, ratio))

        pkgs = heapq.nlargest(4, because, key=attrgetter('ratio'))
        return [pkg for pkg, _ in pkgs]

    def get_prediction(self, limit=0):
        """
        Return prediction based on recommendation size (number of items).
        """
        sorted_result = sorted(self.item_score.items(),
                               key=operator.itemgetter(1))
        if not limit or limit > self.size:
            limit = self.size

        return list(reversed(sorted_result[-limit:]))


class Recommender:
    """
    Class designed to play the role of recommender.
    """
    def __init__(self):
        """
        Set initial parameters.
        """
        self.cfg = Config()
        # Load xapian indexes
        # self.axi_programs = xapian.Database(cfg.axi_programs)
        self.axi_desktopapps = xapian.Database(self.cfg.axi_desktopapps)
        if self.cfg.popcon:
            # self.popcon_programs = xapian.Database(cfg.popcon_programs)
            self.popcon_desktopapps = xapian.Database(
                self.cfg.popcon_desktopapps)
        # Load valid programs, desktopapps and tags
        # format: one package or tag name per line
        # self.valid_programs = []
        self.valid_desktopapps = []
        self.valid_tags = []
        logging.info("Loading recommender filters")
        # with open(os.path.join(cfg.filters_dir,"programs")) as pkgs:
        #    self.valid_programs = [line.strip() for line in pkgs
        #                           if not line.startswith("#")]
        with open(os.path.join(self.cfg.filters_dir, "desktopapps")) as pkgs:
            self.valid_desktopapps = [line.strip() for line in pkgs
                                      if not line.startswith("#")]
        with open(os.path.join(self.cfg.filters_dir, "debtags")) as tags:
            self.valid_tags = [line.strip() for line in tags
                               if not line.startswith("#")]
        # Set xapian index weighting scheme
        if self.cfg.weight == "bm25":
            self.weight = xapian.BM25Weight(self.cfg.bm25_k1, self.cfg.bm25_k2,
                                            self.cfg.bm25_k3, self.cfg.bm25_b,
                                            self.cfg.bm25_nl)
        else:
            self.weight = xapian.TradWeight()
        self.set_strategy(self.cfg.strategy)

    def set_strategy(self, strategy_str, k=0, n=0):
        """
        Set the recommendation strategy.
        """
        if k:
            k_neighbors = k
        else:
            k_neighbors = self.cfg.k_neighbors
        if n:
            profile_size = n
        else:
            profile_size = self.cfg.profile_size
        logging.info("Setting recommender strategy to \'%s\'" % strategy_str)
        # Check if collaborative strategies can be instanciated
        if "knn" in strategy_str:
            if not self.cfg.popcon:
                logging.info("Cannot perform collaborative strategy")
                return 1
        # if self.cfg.pkgs_filter.split("/")[-1] == "desktopapps":
        self.items_repository = self.axi_desktopapps
        self.valid_pkgs = self.valid_desktopapps
        if "knn" in strategy_str:
            self.users_repository = self.popcon_desktopapps
        # else:
        #    self.items_repository = self.axi_programs
        #    self.valid_pkgs = self.valid_programs
        #    if "knn" in strategy_str:
        #        self.users_repository = self.popcon_programs
        # Set strategy based on strategy_str

        if strategy_str == "cb":
            self.strategy = strategy.ContentBased("mix", profile_size)
        elif strategy_str == "cbt":
            self.strategy = strategy.ContentBased("tag", profile_size)
        elif strategy_str == "cbd":
            self.strategy = strategy.ContentBased("desc", profile_size)
        elif strategy_str == "cbh":
            self.strategy = strategy.ContentBased("half", profile_size)
        elif strategy_str == "cbtm":
            self.strategy = strategy.ContentBased("time", profile_size)
        elif strategy_str == "mlbva":
            self.strategy = strategy.MachineLearningBVA("mlbva_mix",
                                                        profile_size)
        elif strategy_str == "mlbow":
            self.strategy = strategy.MachineLearningBOW("mlbow_mix",
                                                        profile_size)
        elif strategy_str == "mlbva_eset":
            self.strategy = strategy.MachineLearningBVA("mlbva_mix_eset",
                                                        profile_size)
        elif strategy_str == "mlbow_eset":
            self.strategy = strategy.MachineLearningBOW("mlbow_mix_eset",
                                                        profile_size)
        elif strategy_str == "cb_eset":
            self.strategy = strategy.ContentBased("mix_eset", profile_size)
        elif strategy_str == "cbt_eset":
            self.strategy = strategy.ContentBased("tag_eset", profile_size)
        elif strategy_str == "cbd_eset":
            self.strategy = strategy.ContentBased("desc_eset", profile_size)
        elif strategy_str == "cbh_eset":
            self.strategy = strategy.ContentBased("half_eset", profile_size)
        elif strategy_str == "knn":
            self.strategy = strategy.Knn(k_neighbors)
        elif strategy_str == "knn_plus":
            self.strategy = strategy.KnnPlus(k_neighbors)
        elif strategy_str == "knn_eset":
            self.strategy = strategy.KnnEset(k_neighbors)
        elif strategy_str == "knnco":
            self.strategy = strategy.KnnContent(k_neighbors)
        elif strategy_str == "knnco_eset":
            self.strategy = strategy.KnnContentEset(k_neighbors)
        # [FIXME: fix repository instanciation]
        # elif strategy_str.startswith("demo"):
        #    self.strategy = strategy.Demographic(strategy_str)
        else:
            logging.info("Strategy not defined.")
            self.strategy = None

    def get_recommendation(self, user, result_size=100):
        """
        Produces recommendation using previously loaded strategy.
        """
        if self.strategy is None:
            return ""

        return self.strategy.run(self, user, result_size)
