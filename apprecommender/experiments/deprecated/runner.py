#!/usr/bin/env python
"""
    recommender suite - recommender experiments suite
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

import expsuite
import sys
import logging
import random
import Gnuplot

sys.path.insert(0, '../')

from config import Config
from data import PopconXapianIndex
from recommender import Recommender, RecommendationResult
from evaluation import Evaluation, Accuracy, Precision, Recall, F1
from user import LocalSystem, User


class ClusteringSuite(expsuite.PyExperimentSuite):

    def reset(self, params, rep):
        self.cfg = Config()
        self.cfg.popcon_index = "../tests/test_data/.sample_pxi"
        self.cfg.popcon_dir = "../tests/test_data/popcon_dir"
        self.cfg.clusters_dir = "../tests/test_data/clusters_dir"

        if params['name'] == "clustering":
            logging.info("Starting 'clustering' experiments suite...")
            self.cfg.index_mode = "recluster"

    def iterate(self, params, rep, n):
        if params['name'] == "clustering":
            logging.info("Running iteration %d" % params['medoids'][n])
            self.cfg.k_medoids = params['medoids'][n]
            pxi = PopconXapianIndex(self.cfg)
            result = {'k_medoids': params['medoids'][n],
                      'dispersion': pxi.cluster_dispersion}
        else:
            result = {}
        return result


class ContentBasedSuite(expsuite.PyExperimentSuite):

    def reset(self, params, rep):
        if params['name'].startswith("content"):
            cfg = Config()
            # if the index was not built yet
            # app_axi = AppAptXapianIndex(cfg.axi,"results/arnaldo/AppAxi")
            cfg.axi = "data/AppAxi"
            cfg.index_mode = "old"
            cfg.weight = params['weight']
            self.rec = Recommender(cfg)
            self.rec.set_strategy(params['strategy'])
            self.repo_size = self.rec.items_repository.get_doccount()
            self.user = LocalSystem()
            self.user.app_pkg_profile(self.rec.items_repository)
            self.sample_size = int(
                len(self.user.pkg_profile) * params['sample'])
            # iteration should be set to 10 in config file
            # self.profile_size = range(10,101,10)

    def iterate(self, params, rep, n):
        if params['name'].startswith("content"):
            item_score = dict.fromkeys(self.user.pkg_profile, 1)
            # Prepare partition
            sample = {}
            for i in range(self.sample_size):
                key = random.choice(item_score.keys())
                sample[key] = item_score.pop(key)
            # Get full recommendation
            user = User(item_score)
            recommendation = self.rec.get_recommendation(user, self.repo_size)
            # Write recall log
            recall_file = "results/content/recall/%s-%s-%.2f-%d" % \
                          (params['strategy'], params[
                           'weight'], params['sample'], n)
            output = open(recall_file, 'w')
            output.write("# weight=%s\n" % params['weight'])
            output.write("# strategy=%s\n" % params['strategy'])
            output.write("# sample=%f\n" % params['sample'])
            output.write("\n%d %d %d\n" %
                         (self.repo_size, len(item_score), self.sample_size))
            notfound = []
            ranks = []
            for pkg in sample.keys():
                if pkg in recommendation.ranking:
                    ranks.append(recommendation.ranking.index(pkg))
                else:
                    notfound.append(pkg)
            for r in sorted(ranks):
                output.write(str(r) + "\n")
            if notfound:
                output.write("Out of recommendation:\n")
                for pkg in notfound:
                    output.write(pkg + "\n")
            output.close()
            # Plot metrics summary
            accuracy = []
            precision = []
            recall = []
            f1 = []
            g = Gnuplot.Gnuplot()
            g('set style data lines')
            g.xlabel('Recommendation size')
            for size in range(1, len(recommendation.ranking) + 1, 100):
                predicted = RecommendationResult(
                    dict.fromkeys(recommendation.ranking[:size], 1))
                real = RecommendationResult(sample)
                evaluation = Evaluation(predicted, real, self.repo_size)
                accuracy.append([size, evaluation.run(Accuracy())])
                precision.append([size, evaluation.run(Precision())])
                recall.append([size, evaluation.run(Recall())])
                f1.append([size, evaluation.run(F1())])
            g.plot(Gnuplot.Data(accuracy, title="Accuracy"),
                   Gnuplot.Data(precision, title="Precision"),
                   Gnuplot.Data(recall, title="Recall"),
                   Gnuplot.Data(f1, title="F1"))
            g.hardcopy(recall_file + "-plot.ps", enhanced=1, color=1)
            # Iteration log
            result = {'iteration': n,
                      'weight': params['weight'],
                      'strategy': params['strategy'],
                      'accuracy': accuracy[20],
                      'precision': precision[20],
                      'recall:': recall[20],
                      'f1': f1[20]}
            return result

# class CollaborativeSuite(expsuite.PyExperimentSuite):
#    def reset(self, params, rep):
#        if params['name'].startswith("collaborative"):
#
#    def iterate(self, params, rep, n):
#        if params['name'].startswith("collaborative"):
#            for root, dirs, files in os.walk(self.source_dir):
#                for popcon_file in files:
#                    submission = PopconSubmission(
#                        os.path.join(root,popcon_file))
#                    user = User(submission.packages)
#                    user.maximal_pkg_profile()
#                    rec.get_recommendation(user)
#                    precision = 0
#                    result = {'weight': params['weight'],
#                              'strategy': params['strategy'],
#                              'profile_size': self.profile_size[n],
#                              'accuracy': accuracy,
#                              'precision': precision,
#                              'recall:': recall,
#                              'f1': }
#        else:
#            result = {}
#        return result

if __name__ == '__main__':

    if "clustering" in sys.argv or len(sys.argv) < 3:
        ClusteringSuite().start()
    if "content" in sys.argv or len(sys.argv) < 3:
        ContentBasedSuite().start()
    # if "collaborative" in sys.argv or len(sys.argv)<3:
    # CollaborativeSuite().start()
