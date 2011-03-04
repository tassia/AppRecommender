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

import random
from collections import defaultdict
from user import *
from recommender import *

class Metric:
    """  """

class Precision(Metric):
    """  """
    def __init__(self):
        self.desc = " Precision "

    def run(self,evaluation):
        return float(len(evaluation.predicted_real) /
                     len(evaluation.predicted_relevant))

class Recall(Metric):
    """  """
    def __init__(self):
        self.desc = "   Recall  "

    def run(self,evaluation):
        return float(len(evaluation.predicted_real) /
                     len(evaluation.real_relevant))

class F1(Metric):
    """  """
    def __init__(self):
        self.desc = "     F1    "

    def run(self,evaluation):
        p = Precision().run(evaluation)
        r = Recall().run(evaluation)
        return float((2*p*r)/(p+r))

class MAE(Metric):
    """  """
    def __init__(self):
        self.desc = "    MAE    "

    def run(self,evaluation):
        print "run"

class MSE(Metric):
    """  """
    def __init__(self):
        self.desc = "    MSE    "

    def run(self,evaluation):
        print "run"

class Coverage(Metric):
    """  """
    def __init__(self):
        self.desc = "  Coverage "

    def run(self,evaluation):
        print "run"

class Evaluation:
    """  """
    def __init__(self,predicted_result,real_result):
        """  """
        self.predicted_item_scores = predicted_result.item_score
        self.predicted_relevant = predicted_result.get_prediction()
        self.real_item_scores = real_result.item_score
        self.real_relevant = real_result.get_prediction()
        self.predicted_real = [v for v in self.predicted_relevant if v in
                               self.real_relevant]

    def run(self,metric):
        return metric.run(self)

class CrossValidation:
    """ Cross-validation method """
    def __init__(self,partition_proportion,rounds,rec,metrics_list):
        """ Set parameters: partition_size, rounds, recommender and
        metrics_list """
        if partition_proportion<1 and partition_proportion>0:
            self.partition_proportion = partition_proportion
        else:
            print "A proporcao de particao deve ser um avalor ente 0 e 1."
            exit(1)
        self.rounds = rounds
        self.recommender = rec
        self.metrics_list = metrics_list
        self.cross_results = defaultdict(list)

    def print_result(self):
        print ""
        metrics_desc = ""
        for metric in self.metrics_list:
            metrics_desc += "%s|" % (metric.desc)
        print "| Round |%s" % metrics_desc
        for r in range(self.rounds):
            metrics_result = ""
            for metric in self.metrics_list:
                metrics_result += ("    %.2f   |" %
                                   (self.cross_results[metric.desc][r]))
            print "|   %d   |%s" % (r,metrics_result)
        metrics_mean = ""
        for metric in self.metrics_list:
            mean = float(sum(self.cross_results[metric.desc]) /
                         len(self.cross_results[metric.desc]))
            metrics_mean += "    %.2f   |" % (mean)
        print "|  Mean |%s" % (metrics_mean)

    def run(self,user):
        """ Perform cross-validation. """
        partition_size = int(len(user.item_score)*self.partition_proportion)
        cross_item_score = user.item_score.copy()
        for r in range(self.rounds):
            round_partition = {}
            for j in range(partition_size):
                if len(cross_item_score)>0:
                    random_key = random.choice(cross_item_score.keys())
                else:
                    print "cross_item_score vazio"
                    exit(1)
                round_partition[random_key] = cross_item_score.pop(random_key)
            round_user = User(cross_item_score)
            predicted_result = self.recommender.generate_recommendation(round_user)
            real_result = RecommendationResult(round_partition,len(round_partition))
            evaluation = Evaluation(predicted_result,real_result)
            for metric in self.metrics_list:
                result = evaluation.run(metric)
                self.cross_results[metric.desc].append(result)
            while len(round_partition)>0:
                item,score = round_partition.popitem()
                cross_item_score[item] = score
        self.print_result()

