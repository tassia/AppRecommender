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

import xapian
from data import *
from recommender import *

class ReputationHeuristic:
    """ Abstraction for diferent reputation heuristics. """

class BugsHeuristic(ReputationHeuristic):
    """ Reputation heuristic based on quantity of open bugs. """

class RCBugsHeuristic(ReputationHeuristic):
    """ Reputation heuristic based on quantity of RC bugs. """

class PopularityHeuristic(ReputationHeuristic):
    """ Reputation heuristic based on popularity of packages. """


class PkgMatchDecider(xapian.MatchDecider):
    """ Extends xapian.MatchDecider to disconsider installed packages. """

    def __init__(self, installed_pkgs):
        xapian.MatchDecider.__init__(self)
        self.installed_pkgs = installed_pkgs

    def __call__(self, doc):
        return doc.get_data() not in self.installed_pkgs


class RecommendationStrategy:
    """ Abstraction for diferent recommendation strategy. """

class ItemReputationStrategy(RecommendationStrategy):
    """ Recommendation strategy based on items reputation. """
    def run(self,items_list,heuristic):
        """  """
        return RecomendationResult()

class ContentBasedStrategy(RecommendationStrategy):
    """ Content-based recommendation strategy. """
    #def __init__(self,items_repository):
    #    self.items_repository = items_repository
    def __init__(self,reindex):
        self.reindex = reindex

    def run(self,recommender,user):
        """  """
        best_tags = recommender.items_repository.get_relevant_tags(user.items(),
                                                                   50)
        debtags_index = DebtagsIndex(
                        os.path.expanduser("~/.app-recommender/debtags_index"))
        debtags_index.load(recommender.items_repository,self.reindex)

        qp = xapian.QueryParser()
        query = qp.parse_query(best_tags)
        enquire = xapian.Enquire(debtags_index.index)
        enquire.set_query(query)

        mset = enquire.get_mset(0, 20, None, PkgMatchDecider(user.items()))
        item_score = {}
        for m in mset:
            item_score[m.document.get_data()] = m.rank
        return RecommendationResult(item_score,20)

class ColaborativeStrategy(RecommendationStrategy):
    """ Colaborative recommendation strategy. """
    def run(self,user,users_repository,similarity_measure):
        """  """
        return RecomendationResult()

class KnowledgeBasedStrategy(RecommendationStrategy):
    """ Knowledge-based recommendation strategy. """
    def run(self,user,knowledge_repository):
        """  """
        return RecomendationResult()

class DemographicStrategy(RecommendationStrategy):
    """ Recommendation strategy based on demographic data. """
    def run(self,user,items_repository):
        """  """
        return RecomendationResult()
