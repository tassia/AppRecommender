#!/usr/bin/python

#  recommender - python module for classes related to recommenders.
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

from operator import itemgetter
from data import *
from strategy import *
from error import Error

class RecommendationResult:
    """
    Class designed to describe a recommendation result: items and scores.
    """
    def __init__(self,item_score,size):
        """
        Set initial parameters.
        """
        self.item_score = item_score
        self.size = size

    def __str__(self):
        """
        String representation of the object.
        """
        result = self.get_prediction()
        str = "\n"
        for i in range(len(result)):
            str += "%2d: %s\n" % (i,result[i][0])
        return str

    def get_prediction(self):
        """
        Return prediction based on recommendation size (number of items).
        """
        sorted_result = sorted(self.item_score.items(), key=itemgetter(1))
        return sorted_result[:self.size]

class Recommender:
    """
    Class designed to play the role of recommender.
    """
    def __init__(self,cfg):
        """
        Set initial parameters.
        """
        try:
            strategy = "self."+cfg.strategy+"(cfg)"
            exec(strategy)
        except (NameError, AttributeError, SyntaxError):
            logging.critical("Could not perform recommendation strategy '%s'" %
                              cfg.strategy)
            raise Error

    def ct(self,cfg):
        """
        Perform content-based recommendation using tags index as source data.
        """
        self.items_repository = TagsXapianIndex(cfg)
        self.strategy = ContentBasedStrategy()

    def cta(self,cfg):
        """
        Perform content-based recommendation using apt-xapian-index as source
        data.
        """
        self.items_repository = xapian.Database(cfg.axi)
        self.strategy = AxiContentBasedStrategy()

    def set_strategy(self,strategy):
        """
        Set the recommendation strategy.
        """
        self.strategy = strategy

    def get_recommendation(self,user):
        """
        Produces recommendation using previously loaded strategy.
        """
        return self.strategy.run(self,user)
