#!/usr/bin/python

#  evaluation - python module for classes and methods related to recommenders
#               evaluation.
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
import logging

from user import *
from recommender import *
from singleton import Singleton

class Metric(Singleton):
    """
    Base class for metrics. Strategy design pattern.
    """
    pass

class Precision(Metric):
    """
    Classification accuracy metric defined as the percentage of relevant itens
    among the predicted ones.
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "  Precision  "

    def run(self,evaluation):
        """
        Compute metric.
        """
        return float(len(evaluation.predicted_real))/len(evaluation.predicted_relevant)

class Recall(Metric):
    """
    Classification ccuracy metric defined as the percentage of relevant itens
    which were predicted as so.
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "    Recall   "

    def run(self,evaluation):
        """
        Compute metric.
        """
        return float(len(evaluation.predicted_real))/len(evaluation.real_relevant)

class F1(Metric):
    """
    Classification accuracy metric which correlates precision and recall into an
    unique measure.
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "      F1     "

    def run(self,evaluation):
        """
        Compute metric.
        """
        p = Precision().run(evaluation)
        r = Recall().run(evaluation)
        return float((2*p*r))/(p+r)

class MAE(Metric):
    """
    Prediction accuracy metric defined as the mean absolute error.
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "     MAE     "

    def get_errors(self,evaluation):
        """
        Compute prediction errors.
        """
        keys = evaluation.predicted_item_scores.keys()
        keys.extend(evaluation.real_item_scores.keys())
        errors = []
        for k in keys:
            if k not in evaluation.real_item_scores:
                evaluation.real_item_scores[k] = 0.0
            if k not in evaluation.predicted_item_scores:
                evaluation.predicted_item_scores[k] = 0.0
            errors.append(float(evaluation.predicted_item_scores[k]-
                          evaluation.real_item_scores[k]))
        return errors

    def run(self,evaluation):
        """
        Compute metric.
        """
        errors = self.get_errors(evaluation)
        return sum(errors)/len(errors)

class MSE(MAE):
    """
    Prediction accuracy metric defined as the mean square error. 
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "     MSE     "

    def run(self,evaluation):
        """
        Compute metric.
        """
        errors = self.get_errors(evaluation)
        square_errors = [pow(x,2) for x in errors]
        return sum(square_errors)/len(square_errors)

class Coverage(Metric):
    """
    Evaluation metric defined as the percentage of itens covered by the
    recommender (have been recommended at least once).
    """
    def __init__(self,repository_size):
        """
        Set initial parameters.
        """
        self.desc = "   Coverage  "
        self.repository_size = repository_size
        self.covered = set()

    def save_covered(self,recommended_list):
        """
        Register that a list of itens has been recommended.
        """
        self.covered.update(set(recommended_list))

    def run(self,evaluation):
        """
        Compute metric.
        """
        return float(self.covered.size)/self.repository_size

class Evaluation:
    """
    Class designed to perform prediction evaluation, given data and metric.
    """
    def __init__(self,predicted_result,real_result):
        """
        Set initial parameters.
        """
        self.predicted_item_scores = predicted_result.item_score
        self.predicted_relevant = predicted_result.get_prediction()
        self.real_item_scores = real_result.item_score
        self.real_relevant = real_result.get_prediction()
        self.predicted_real = [v for v in self.predicted_relevant if v in
                               self.real_relevant]
        #print len(self.predicted_relevant)
        #print len(self.real_relevant)
        #print len(self.predicted_real)

    def run(self,metric):
        """
        Perform the evaluation with the given metric.
        """
        return metric.run(self)

class CrossValidation:
    """
    Class designed to perform cross-validation process.
    """
    def __init__(self,partition_proportion,rounds,rec,metrics_list):
        """
        Set initial parameters.
        """
        if partition_proportion<1 and partition_proportion>0:
            self.partition_proportion = partition_proportion
        else:
            logging.critical("Partition proportion must be a value in the interval [0,1].")
            raise Error
        self.rounds = rounds
        self.recommender = rec
        self.metrics_list = metrics_list
        self.cross_results = defaultdict(list)

    def __str__(self):
        """
        String representation of the object.
        """
        str = "\n"
        metrics_desc = ""
        for metric in self.metrics_list:
            metrics_desc += "%s|" % (metric.desc)
        str += "| Round |%s\n" % metrics_desc
        for r in range(self.rounds):
            metrics_result = ""
            for metric in self.metrics_list:
                metrics_result += ("     %2.1f%%    |" %
                                   (self.cross_results[metric.desc][r]*100))
            str += "|   %d   |%s\n" % (r,metrics_result)
        metrics_mean = ""
        for metric in self.metrics_list:
            mean = float(sum(self.cross_results[metric.desc]) /
                         len(self.cross_results[metric.desc]))
            metrics_mean += "     %2.1f%%    |" % (mean*100)
        str += "|  Mean |%s\n" % (metrics_mean)
        return str

    def run(self,user):
        """
        Perform cross-validation.
        """
        cross_item_score = dict.fromkeys(user.pkg_profile,1)
        partition_size = int(len(cross_item_score)*self.partition_proportion)
        for r in range(self.rounds):
            round_partition = {}
            for j in range(partition_size):
                if len(cross_item_score)>0:
                    random_key = random.choice(cross_item_score.keys())
                else:
                    logging.critical("Empty cross_item_score.")
                    raise Error
                round_partition[random_key] = cross_item_score.pop(random_key)
            round_user = User(cross_item_score)
            predicted_result = self.recommender.get_recommendation(round_user)
            real_result = RecommendationResult(round_partition,len(round_partition))
            evaluation = Evaluation(predicted_result,real_result)
            for metric in self.metrics_list:
                result = evaluation.run(metric)
                self.cross_results[metric.desc].append(result)
            while len(round_partition)>0:
                item,score = round_partition.popitem()
                cross_item_score[item] = score

