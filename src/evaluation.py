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

class Metric:
    """  """

class Precision(Metric):
    """  """
    def __init_(self):
        self.desc = "Precision"

    def run(self,evaluation):
        return float(len(evaluation.predicted_real) /
                     len(evaluation.predicted_relevant))

class Recall(Metric):
    """  """
    def __init_(self):
        self.desc = "Recall"

    def run(self,evaluation):
        return float(len(evaluation.predicted_real) /
                     len(evaluation.real_relevant))

class F1(Metric):
    """  """
    def __init_(self):
        self.desc = "F1"

    def run(self,evaluation):
        p = Precision().run(evaluation)
        r = Recall().run(evaluation)
        return float((2*p*r)/(p+r))

class MAE(Metric):
    """  """
    def __init_(self):
        self.desc = "MAE"

    def run(self,evaluation):
        print "run"

class MSE(Metric):
    """  """
    def __init_(self):
        self.desc = "MSE"

    def run(self,evaluation):
        print "run"

class Coverage(Metric):
    """  """
    def __init_(self):
        self.desc = "Coverage"

    def run(self,evaluation):
        print "run"

class Evaluation:
    """  """
    def __init__(self,predicted_result,real_result):
        """  """
        self.predicted_item_scores = predicted_result.item_score
        self.predicted_relevant = predicted_result.get_prediction.keys()
        self.real_item_scores = real_result.item_score
        self.real_relevant = real_result.get_prediction.keys()
        self.predicted_real = [v for v in self.predicted_relevant if v in
                               self.real_relevant]

    def run(self,metric):
        return metric.run(self)

class CrossValidation:
    """ Cross-validation method """
    def __init__(self,partition_size,rounds,rec,metrics_list):
        """ Set parameters: partition_size, rounds, recommender and
        metrics_list """
        self.partition_size = partition_size
        self.rounds = rounds
        self.recommender = rec
        self.metrics_list = self.metrics_list

    def run(self,user):
        """ Perform cross-validation. """
        for i in rounds:
            cross_result = {}
            for metric in self.metrics_list:
                cross_results[metric.desc] = []
            cross_user = User(user.item_score) # FIXME: choose subset
            predicted_result = self.recommender.gererateRecommendation()
            evaluation = Evaluation(predicted_result,user.item_score)
            for metric in self.metrics_list:
                cross_results[metric.desc].append(evaluation.run(metric))
        for metric in self.metrics_list:
            mean = (sum(cross_result[metric.desc]) /
                    len(cross_result[metric.desc]))
            print "Mean %d: %2f" % (metric.desc,mean)

