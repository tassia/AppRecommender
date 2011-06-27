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

import xapian
import operator
import data
import strategy

class RecommendationResult:
    """
    Class designed to describe a recommendation result: items and scores.
    """
    def __init__(self,item_score):
        """
        Set initial parameters.
        """
        self.item_score = item_score

    def __str__(self):
        """
        String representation of the object.
        """
        result = self.get_prediction()
        str = "\n"
        for i in range(len((list(result)))):
            str += "%2d: %s\n" % (i,result[i][0])
        return str

    def get_prediction(self,size=20):
        """
        Return prediction based on recommendation size (number of items).
        """
        if size > len(self.item_score): size = len(self.item_score)
        sorted_result = sorted(self.item_score.items(),
                               key=operator.itemgetter(1))
        return list(reversed(sorted_result[-size:]))

class Recommender:
    """
    Class designed to play the role of recommender.
    """
    def __init__(self,cfg):
        """
        Set initial parameters.
        """
        self.items_repository = xapian.Database(cfg.axi)
        self.users_repository = data.PopconXapianIndex(cfg) #[FIXME] only cfg fields
        self.clustered_users_repository = data.PopconXapianIndex(cfg) #[FIXME]
        self.set_strategy(cfg.strategy)
        if cfg.weight == "bm25":
            self.weight = xapian.BM25Weight()
        else:
            self.weight = xapian.TradWeight()

    def set_strategy(self,strategy_str):
        """
        Set the recommendation strategy.
        """
        if strategy_str == "cb":
            self.strategy = strategy.ContentBasedStrategy("full")
        if strategy_str == "cbt":
            self.strategy = strategy.ContentBasedStrategy("tag")
        if strategy_str == "cbd":
            self.strategy = strategy.ContentBasedStrategy("desc")
        if strategy_str == "col":
            self.strategy = strategy.CollaborativeStrategy(20)

    def get_recommendation(self,user,limit=20):
        """
        Produces recommendation using previously loaded strategy.
        """
        return self.strategy.run(self,user,limit)
