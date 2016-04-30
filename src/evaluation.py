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
import logging

from abc import ABCMeta, abstractmethod
from collections import defaultdict
from error import Error
from singleton import Singleton
from recommender import RecommendationResult
from user import User
from data import split_pkg_data


class Metric(Singleton):

    """
    Base class for metrics. Strategy design pattern.
    """

    def get_errors(self, evaluation):
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
            errors.append(float(evaluation.predicted_item_scores[k] -
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

    def run(self, evaluation):
        """
        Compute metric.
        """
        simple_accurary = float((evaluation.repository_size -
                                evaluation.false_positive_len) -
                                evaluation.false_negative_len)

        return simple_accurary / evaluation.repository_size


class Accuracy(Metric):

    """
    Classification accuracy metric which consider classes sizes.
    """

    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "    Accuracy  "

    def run(self, evaluation):
        """
        Compute metric.
        """
        error_1 = (float(evaluation.false_positive_len) /
                        (evaluation.repository_size -
                         evaluation.real_relevant_len))
        error_2 = (float(evaluation.false_negative_len) /
                   evaluation.real_relevant_len)
        accuracy = 1 - (float(error_1 + error_2) / 2)
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

    def run(self, evaluation):
        """
        Compute metric.
        """
        precision = float(evaluation.true_positive_len)

        if not precision:
            return 0.0

        return precision / float(evaluation.predicted_relevant_len)


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

    def run(self, evaluation):
        """
        Compute metric.
        """
        recall = float(evaluation.true_positive_len)

        if not recall:
            return 0.0

        return recall / evaluation.real_relevant_len


class FPR(Metric):

    """
    False positive rate (used for ploting ROC curve).
    """

    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "    FPR    "

    def run(self, evaluation):
        """
        Compute metric.
        """

        if not evaluation.false_positive_len:
            return 0.0

        return (float(evaluation.false_positive_len) /
                evaluation.real_negative_len)


class MCC(Metric):

    """
    Matthews correlation coefficient.
    """

    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "    MCC    "

    def run(self, evaluation):
        """
        Compute metric.
        """
        VP = evaluation.true_positive_len
        FP = evaluation.false_positive_len
        FN = evaluation.false_negative_len
        VN = evaluation.true_negative_len

        if ((VP + FP) == 0 or (VP + FN) == 0 or
           (VN + FP) == 0 or (VN + FN) == 0):
            return 0

        MCC = (((VP * VN) - (FP * FN)) /
               math.sqrt((VP + FP) * (VP + FN) * (VN + FP) * (VN + FN)))

        return MCC


class F_score(Metric):

    """
    Classification accuracy metric which correlates precision and
    recall into an unique measure.
    """

    def __init__(self, k):
        """
        Set metric description.
        """
        self.desc = "  F(%.1f)  " % k
        self.k = k

    def run(self, evaluation):
        """
        Compute metric.
        """
        p = Precision().run(evaluation)
        r = Recall().run(evaluation)
        if ((self.k * self.k * p) + r) > 0:
            return float(((1 + (self.k * self.k)) * ((p * r) /
                         ((self.k * self.k * p) + r))))
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

    def run(self, evaluation):
        """
        Compute metric.
        """
        errors = self.get_errors(evaluation)
        return sum(errors) / len(errors)


class MSE(Metric):

    """
    Prediction accuracy metric defined as the mean square error.
    """

    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "     MSE     "

    def run(self, evaluation):
        """
        Compute metric.
        """
        errors = self.get_errors(evaluation)
        square_errors = [pow(x, 2) for x in errors]
        return sum(square_errors) / len(square_errors)


class RMSE(MSE):

    """
    Prediction accuracy metric defined as the root mean square error.
    """

    def __init__(self):
        """
        Set metric description.
        """
        self.desc = "     RMSE     "

    def run(self, evaluation):
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

    def run(self, evaluations_set):
        """
        Compute metric.
        """
        covered = set()
        for evaluation in evaluations_set:
            covered.update(set(evaluation.predicted_relevant))
        return float(len(covered)) / evaluation.repository_size


class Evaluation:

    """
    Class designed to perform prediction evaluation, given data and metric.
    """

    def __init__(self, predicted, real, repository_size):
        """
        Set initial parameters.
        """
        self.repository_size = repository_size
        self.predicted_item_scores = predicted.item_score

        self.predicted_relevant = predicted.get_prediction()
        self.predicted_relevant_len = len(self.predicted_relevant)

        self.real_item_scores = real.item_score
        self.real_relevant = real.get_prediction()
        self.real_relevant_len = len(self.real_relevant)

        self.true_positive = [v[0] for v in self.predicted_relevant if v[0] in
                              [w[0] for w in self.real_relevant]]
        self.false_positive = [v[0] for v in self.predicted_relevant
                               if not v[0] in [w[0]
                               for w in self.real_relevant]]
        self.false_negative = [v[0] for v in self.real_relevant if not v[0] in
                               [w[0] for w in self.predicted_relevant]]

        self.true_positive_len = len(self.true_positive)
        self.false_positive_len = len(self.false_positive)
        self.false_negative_len = len(self.false_negative)
        self.real_negative_len = self.repository_size - self.real_relevant_len
        self.true_negative_len = (self.real_negative_len -
                                  len(self.false_positive))
        logging.debug("TP: %d" % len(self.true_positive))
        logging.debug("FP: %d" % len(self.false_positive))
        logging.debug("FN: %d" % len(self.false_negative))
        logging.debug("TN: %d" % self.true_negative_len)
        logging.debug("Repo_size: %d" % self.repository_size)
        logging.debug("Relevant: %d" % len(self.real_relevant))
        logging.debug("Irrelevant: %d" % self.real_negative_len)

    def run(self, metric):
        """
        Perform the evaluation with the given metric.
        """
        return metric.run(self)


class CrossValidation:

    __metaclass__ = ABCMeta

    """
    Class designed to perform cross-validation process.

    :param partition_proportion: A value that should dictates the number of
                                 data that will be on the traning data, the
                                 rest of data will be used as the validation
                                 set.
    :param rounds:               The number of rounds that cross validation
                                 will be used on.
    :param rec:                  The recommendation strategy used.
    :param metrics_list:         Array of the metrics that will be used to
                                 evaluate the algorithm.
    :param result_proportion:    The percentage of recommendations that should
                                 be used based on the total number of packages
                                 available.
    """

    def __init__(self, partition_proportion, rounds, rec,
                 metrics_list, result_proportion):
        """
        Set initial parameters.
        """
        if partition_proportion < 1 and partition_proportion > 0:
            self.partition_proportion = partition_proportion
        else:
            logging.critical("Partition proportion must be a value"
                             "in the interval [0,1].")
            raise Error
        self.rounds = rounds
        self.recommender = rec
        self.metrics_list = metrics_list
        self.cross_results = defaultdict(list)
        self.result_proportion = result_proportion

    @abstractmethod
    def get_evaluation(self, predicted_result, real_result):
        raise NotImplementedError("Method not implemented.")

    @abstractmethod
    def get_model(self):
        raise NotImplementedError("Method not implemented.")

    def get_result_size(self):
        result_size = (self.recommender.items_repository.get_doccount() *
                       self.result_proportion)
        result_size = int(result_size)

        logging.debug("size %d" % result_size)
        return result_size

    @abstractmethod
    def get_real_results(self, round_partition):
        raise NotImplementedError("Method not implemented.")

    def get_partition_size(self, cross_item_score):
        return int(len(cross_item_score) * self.partition_proportion)

    @abstractmethod
    def get_predicted_results(self, round_user, round_partition, result_size):
        raise NotImplementedError("Method not implemented.")

    @abstractmethod
    def get_user_score(self, user):
        raise NotImplementedError("Method not implemented.")

    def reset_cross_item_score(self, cross_item_score, round_partition):
        while len(round_partition) > 0:
            item, score = round_partition.popitem()
            cross_item_score[item] = score

        return cross_item_score

    def run_metrics(self, predicted_result, real_result):
        logging.debug("Predicted result: %s", predicted_result)

        evaluation = self.get_evaluation(predicted_result, real_result)

        for metric in self.metrics_list:
            result = evaluation.run(metric)
            self.cross_results[metric.desc].append(result)

    def run(self, user):
        """
        Perform cross-validation.
        """

        '''
        A dictionary containing all the usefull user packages.
        Its key is a package name, and its value is the input vector
        associated with that package.
        '''
        cross_item_score = self.get_user_score(user)

        # The amount of data that will be used to train the algorithm
        partition_size = self.get_partition_size(cross_item_score)

        # main iteration
        for r in range(self.rounds):
            round_partition = split_pkg_data(cross_item_score, partition_size)

            logging.debug("Round partition: %s", str(round_partition))
            logging.debug("Cross item-score: %s", str(cross_item_score))

            # The algorithm model created with the selected training data.
            round_model = self.get_model(round_partition)

            result_size = self.get_result_size()
            if not result_size:
                logging.critical("Recommendation size is zero.")
                raise Error

            predicted_result = self.get_predicted_results(
                round_model, cross_item_score, result_size)
            if not predicted_result.size:
                logging.critical("No recommendation produced"
                                 " Abort cross-validation.")
                raise Error
            # partition is considered the expected result
            real_result = self.get_real_results(cross_item_score)

            self.run_metrics(predicted_result, real_result)
            # moving back items from round_partition to cross_item_score
            cross_item_score = self.reset_cross_item_score(cross_item_score,
                                                           round_partition)


class CrossValidationRecommender(CrossValidation):

    def get_evaluation(self, predicted_result, real_result):
        num_docs = self.recommender.items_repository.get_doccount()
        return Evaluation(predicted_result, real_result, num_docs)

    def get_model(self, cross_item_score):
        return User(cross_item_score)

    def get_pkg_score(self, user):
        cross_item_score = {}
        for pkg in user.pkg_profile:
            cross_item_score[pkg] = user.item_score[pkg]

        return cross_item_score

    def get_real_results(self, round_partition):
        return RecommendationResult(round_partition)

    def get_predicted_results(self, round_user, round_partition, result_size):
        return self.recommender.get_recommendation(round_user, result_size)

    def get_user_score(user):
        cross_item_score = {}

        for pkg in user.pkg_profile:
            cross_item_score[pkg] = user.item_score[pkg]

        return cross_item_score

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
                                   (self.cross_results[metric.desc][r] * 100))
            str += "|   %d   |%s\n" % (r, metrics_result)
        metrics_mean = ""
        for metric in self.metrics_list:
            mean = float(sum(self.cross_results[metric.desc]) /
                         len(self.cross_results[metric.desc]))
            metrics_mean += "     %2.1f%%    |" % (mean * 100)
        str += "|  Mean |%s\n" % (metrics_mean)
        return str
