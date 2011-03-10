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

from operator import itemgetter

class RecommendationResult:
    def __init__(self,item_score,size):
        self.item_score = item_score
        self.size = size

    def __str__(self):
        result = self.get_prediction()
        str = "\n"
        for i in range(len(result)):
            str += "%2d: %s\n" % (i,result[i][0])
        return str

    def get_prediction(self):
        sorted_result = sorted(self.item_score.items(), key=itemgetter(1))
        return sorted_result[:self.size]

class Recommender:
    """  """
    def __init__(self,items_repository,users_repository=None,
                 knowledge_repository=None):
        self.items_repository = items_repository
        self.users_repository = users_repository
        self.knowledge_repository = knowledge_repository

    def set_strategy(self,strategy):
        """  """
        self.strategy = strategy

    def get_recommendation(self,user):
        """  """
        return self.strategy.run(self,user)
