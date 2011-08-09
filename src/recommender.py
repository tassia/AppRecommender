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

import logging
import os
import xapian
import operator
import data
import strategy

class RecommendationResult:
    """
    Class designed to describe a recommendation result: items and scores.
    """
    def __init__(self,item_score,ranking=0):
        """
        Set initial parameters.
        """
        self.item_score = item_score
        self.size = len(item_score)
        if ranking:
            self.ranking = ranking

    def __str__(self):
        """
        String representation of the object.
        """
        result = self.get_prediction()
        str = "\n"
        for i in range(len((list(result)))):
            str += "%2d: %s\n" % (i,result[i][0])
        return str

    def get_prediction(self,limit=0):
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
    def __init__(self,cfg):
        """
        Set initial parameters.
        """
        self.cfg = cfg
        self.items_repository = xapian.Database(cfg.axi)
        self.set_strategy(cfg.strategy)
        if cfg.weight == "bm25":
            self.weight = xapian.BM25Weight()
        else:
            self.weight = xapian.TradWeight()
        self.valid_pkgs = []
        # file format: one pkg_name per line
        with open(os.path.join(cfg.filters,cfg.pkgs_filter)) as valid_pkgs:
            self.valid_pkgs = [line.strip() for line in valid_pkgs
                               if not line.startswith("#")]

    def set_strategy(self,strategy_str):
        """
        Set the recommendation strategy.
        """
        logging.info("Setting recommender strategy to \'%s\'" % strategy_str)
        self.items_repository = xapian.Database(self.cfg.axi)
        if "desktop" in strategy_str:
            self.items_repository = xapian.Database("/root/.app-recommender/axi_desktop")
            self.cfg.popcon_index = "/root/.app-recommender/popcon-index_desktop_1000"

        if strategy_str == "cb" or strategy_str == "cb_desktop":
            self.strategy = strategy.ContentBasedStrategy("full",
                                                          self.cfg.profile_size)
        if strategy_str == "cbt" or strategy_str == "cbt_desktop":
            self.strategy = strategy.ContentBasedStrategy("tag",
                                                          self.cfg.profile_size)
        if strategy_str == "cbd" or strategy_str == "cbd_desktop":
            self.strategy = strategy.ContentBasedStrategy("desc",
                                                          self.cfg.profile_size)
        if "col" in strategy_str:
            self.users_repository = data.PopconXapianIndex(self.cfg)
            self.strategy = strategy.CollaborativeStrategy(self.cfg.k_neighbors)

    def get_recommendation(self,user,result_size=100):
        """
        Produces recommendation using previously loaded strategy.
        """
        return self.strategy.run(self,user,result_size)
