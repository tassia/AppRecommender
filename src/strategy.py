#!/usr/bin/python

#  AppRecommender - A GNU/Linux application recommender
#
#  Copyright (C) 2010  Tassia Camoes <tassia@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, re
import xapian
from data import *
from recommender import *

class ReputationHeuristic:
    """
    Abstraction for diferent reputation heuristics.
    """

class BugsHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on quantity of open bugs.
    """

class RCBugsHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on quantity of RC bugs.
    """

class PopularityHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on popularity of packages.
    """


class PkgMatchDecider(xapian.MatchDecider):
    """
    Extends xapian.MatchDecider to disconsider installed packages.
    """

    def __init__(self, installed_pkgs):
        xapian.MatchDecider.__init__(self)
        self.installed_pkgs = installed_pkgs

    def __call__(self, doc):
        return doc.get_data() not in self.installed_pkgs


class RecommendationStrategy:
    """
    Abstraction for diferent recommendation strategy.
    """

class ItemReputationStrategy(RecommendationStrategy):
    """
    Recommendation strategy based on items reputation.
    """
    def run(self,items_list,heuristic):
        """
        Perform recommendation strategy.
        """
        return RecomendationResult()

class ContentBasedStrategy(RecommendationStrategy):
    """
    Content-based recommendation strategy.
    """
    def run(self,recommender,user):
        """
        Perform recommendation strategy.
        """
        profile = user.debtags_tag_profile(recommender.items_repository.debtags_db,50)
        qp = xapian.QueryParser()
        query = qp.parse_query(profile)
        enquire = xapian.Enquire(recommender.items_repository)
        enquire.set_query(query)

        mset = enquire.get_mset(0, 20, None, PkgMatchDecider(user.items()))
        item_score = {}
        for m in mset:
            item_score[m.document.get_data()] = m.rank
        return RecommendationResult(item_score,20)

class AxiContentBasedStrategy(RecommendationStrategy):
    """
    Content-based recommendation strategy based on Apt-xapian-index.
    """
    def run(self,recommender,user):
        """
        Perform recommendation strategy.
        """
        profile = user.axi_tag_profile(recommender.items_repository,50)
        query = xapian.Query(xapian.Query.OP_OR,profile)
        enquire = xapian.Enquire(recommender.items_repository)
        enquire.set_query(query)

        mset = enquire.get_mset(0, 20, None, PkgMatchDecider(user.items()))
        item_score = {}
        for m in mset:
            item_score[m.document.get_data()] = m.rank
        return RecommendationResult(item_score,20)

class ColaborativeStrategy(RecommendationStrategy):
    """
    Colaborative recommendation strategy.
    """
    def run(self,user,users_repository,similarity_measure):
        """
        Perform recommendation strategy.
        """
        return RecomendationResult()

class KnowledgeBasedStrategy(RecommendationStrategy):
    """
    Knowledge-based recommendation strategy.
    """
    def run(self,user,knowledge_repository):
        """
        Perform recommendation strategy.
        """
        return RecomendationResult()

class DemographicStrategy(RecommendationStrategy):
    """
    Recommendation strategy based on demographic data.
    """
    def run(self,user,items_repository):
        """
        Perform recommendation strategy.
        """
        return RecomendationResult()
