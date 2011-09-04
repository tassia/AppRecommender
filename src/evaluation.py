#!/usr/bin/env python
"""
    evaluation - python module for classes and methods related to recommenders
                 evaluation.
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

import math
import random
from collections import defaultdict
import logging

from error import Error
from user import *
from recommender import *
from singleton import Singleton

class Metric(Singleton):
    """
    Base class for metrics. Strategy design pattern.
    """
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


class SimpleAccuracy(Metric):
    """
    Classification accuracy metric which consider classes sizes.
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "  S_Accuracy  "

    def run(self,evaluation):
        """
        Compute metric.
        """
        return float((evaluation.repository_size-
                      len(evaluation.false_positive))-
                      len(evaluation.false_negative))/evaluation.repository_size

class Accuracy(Metric):
    """
    Classification accuracy metric which consider classes sizes.
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "    Accuracy  "

    def run(self,evaluation):
        """
        Compute metric.
        """
        error_1 = (float(len(evaluation.false_positive))/
               (evaluation.repository_size-len(evaluation.real_relevant)))
        error_2 = (float(len(evaluation.false_negative))/len(evaluation.real_relevant))
        accuracy = 1-(float(error_1+error_2)/2)
        return accuracy

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
        return float(len(evaluation.true_positive))/len(evaluation.predicted_relevant)

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
        return float(len(evaluation.true_positive))/len(evaluation.real_relevant)

class FPR(Metric):
    """
    False positive rate (used for ploting ROC curve).
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "    FPR    "

    def run(self,evaluation):
        """
        Compute metric.
        """
        return float(len(evaluation.false_positive))/evaluation.true_negatives_len

class F_score(Metric):
    """
    Classification accuracy metric which correlates precision and recall into an
    unique measure.
    """
    def __init__(self,k):
        """
        Set metric description.
        """
        self.desc = "  F_score   "
        self.k = k

    def run(self,evaluation):
        """
        Compute metric.
        """
        p = Precision().run(evaluation)
        r = Recall().run(evaluation)
        if ((self.k*self.k*p)+r)>0:
            return float(((1+(self.k*self.k))*((p*r)/((self.k*self.k*p)+r))))
        else:
            return 0

class MAE(Metric):
    """
    Prediction accuracy metric defined as the mean absolute error.
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "     MAE     "

    def run(self,evaluation):
        """
        Compute metric.
        """
        errors = self.get_errors(evaluation)
        return sum(errors)/len(errors)

class MSE(Metric):
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

class RMSE(MSE):
    """
    Prediction accuracy metric defined as the root mean square error. 
    """
    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "     RMSE     "

    def run(self,evaluation):
        """
        Compute metric.
        """
        return math.sqrt(MSE.run(evaluation))

class Coverage(Metric):
    """
    Evaluation metric defined as the percentage of itens covered by the
    recommender (have been recommended at least once).
    """
    def __init__(self):
        """
        Set initial parameters.
        """
        self.desc = "   Coverage  "

    def run(self,evaluations_set):
        """
        Compute metric.
        """
        covered = set()
        for evaluation in evaluations_set:
            covered.update(set(evaluation.predicted_relevant))
        return float(len(covered))/evaluation.repository_size

class Evaluation:
    """
    Class designed to perform prediction evaluation, given data and metric.
    """
    def __init__(self,predicted,real,repository_size):
        """
        Set initial parameters.
        """
        self.repository_size = repository_size
        self.predicted_item_scores = predicted.item_score
        self.predicted_relevant = predicted.get_prediction()
        self.real_item_scores = real.item_score
        self.real_relevant = real.get_prediction()

        self.true_positive = [v[0] for v in self.predicted_relevant if v[0] in
                              [w[0] for w in self.real_relevant]]
        self.false_positive = [v[0] for v in self.predicted_relevant if not v[0] in
                               [w[0] for w in self.real_relevant]]
        self.false_negative = [v[0] for v in self.real_relevant if not v[0] in
                               [w[0] for w in self.predicted_relevant]]

        self.true_negatives_len = self.repository_size - len(self.real_relevant)
        #logging.debug("TP: %d" % len(self.true_positive))
        #logging.debug("FP: %d" % len(self.false_positive))
        #logging.debug("FN: %d" % len(self.false_negative))
        #logging.debug("Repo_size: %d" % self.repository_size)
        #logging.debug("Relevant: %d" % len(self.real_relevant))

    def run(self,metric):
        """
        Perform the evaluation with the given metric.
        """
        return metric.run(self)

class CrossValidation:
    """
    Class designed to perform cross-validation process.
    """
    def __init__(self,partition_proportion,rounds,rec,metrics_list,result_proportion):
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
        self.result_proportion = result_proportion

    def run(self,user):
        """
        Perform cross-validation.
        """
        # Extracting user profile scores from cross validation
        cross_item_score = {}
        for pkg in user.pkg_profile:
            cross_item_score[pkg] = user.item_score[pkg]
        partition_size = int(len(cross_item_score)*self.partition_proportion)
        # main iteration
        for r in range(self.rounds):
            round_partition = {}
            # move items from cross_item_score to round-partition
            for j in range(partition_size):
                if len(cross_item_score)>0:
                    random_key = random.choice(cross_item_score.keys())
                else:
                    logging.critical("Empty cross_item_score.")
                    raise Error
                round_partition[random_key] = cross_item_score.pop(random_key)
            logging.debug("Round partition: %s",str(round_partition))
            logging.debug("Cross item-score: %s",str(cross_item_score))
            # round user is created with remaining items
            round_user = User(cross_item_score)
            result_size = int(self.recommender.items_repository.get_doccount()*
                              self.result_proportion)
            logging.debug("size %d" % result_size)
            if not result_size:
                logging.critical("Recommendation size is zero.")
                raise Error
            predicted_result = self.recommender.get_recommendation(round_user,result_size)
            if not predicted_result.size:
                logging.critical("No recommendation produced. Abort cross-validation.")
                raise Error
            # partition is considered the expected result
            real_result = RecommendationResult(round_partition)
            logging.debug("Predicted result: %s",predicted_result)
            evaluation = Evaluation(predicted_result,real_result,
                                    self.recommender.items_repository.get_doccount())
            for metric in self.metrics_list:
                result = evaluation.run(metric)
                self.cross_results[metric.desc].append(result)
            # moving back items from round_partition to cross_item_score
            while len(round_partition)>0:
                item,score = round_partition.popitem()
                cross_item_score[item] = score

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

