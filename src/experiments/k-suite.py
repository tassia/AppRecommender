#!/usr/bin/env python
"""
    k-suite - experiment different neighborhood sizes
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

import sys
sys.path.insert(0,'../')
from config import Config
from data import PopconXapianIndex, PopconSubmission
from recommender import Recommender
from user import LocalSystem, User
from evaluation import *
import logging
import random
import Gnuplot
import numpy

def plot_roc(k,roc_points,log_file):
    g = Gnuplot.Gnuplot()
    g('set style data points')
    g.xlabel('False Positive Rate')
    g.ylabel('True Positive Rate')
    g('set xrange [0:1.0]')
    g('set yrange [0:1.0]')
    g.title("Setup: %s-k%d" % (log_file.split("/")[-1],k))
    g.plot(Gnuplot.Data([[0,0],[1,1]],with_="lines lt 7"),
           Gnuplot.Data(roc_points))
    g.hardcopy(log_file+("-k%.3d.png"%k),terminal="png")
    g.hardcopy(log_file+("-k%.3d.ps"%k),terminal="postscript",enhanced=1,color=1)

def plot_summary(precision,f05,mcc,log_file):
    g = Gnuplot.Gnuplot()
    g('set style data lines')
    g.xlabel('Neighborhood (k)')
    g.title("Setup: %s-size20" % (log_file.split("/")[-1]))
    g.plot(Gnuplot.Data([[k,sum(precision[k])/len(precision[k])] for k in precision.keys()],title="P"),
           Gnuplot.Data([[k,sum(f05[k])/len(f05[k])] for k in f05.keys()],title="F05"),
           Gnuplot.Data([[k,sum(mcc[k])/len(mcc[k])] for k in mcc.keys()],title="MCC"))
    g.hardcopy(log_file+(".png"),terminal="png")
    g.hardcopy(log_file+(".ps"),terminal="postscript",enhanced=1,color=1)

class ExperimentResults:
    def __init__(self,repo_size):
        self.repository_size = repo_size
        self.precision = []
        self.recall = []
        self.fpr = []
        self.f05 = []
        self.mcc = []

    def add_result(self,ranking,sample):
        predicted = RecommendationResult(dict.fromkeys(ranking,1))
        real = RecommendationResult(sample)
        evaluation = Evaluation(predicted,real,self.repository_size)
        self.precision.append(evaluation.run(Precision()))
        self.recall.append(evaluation.run(Recall()))
        self.fpr.append(evaluation.run(FPR()))
        self.f05.append(evaluation.run(F_score(0.5)))
        self.mcc.append(evaluation.run(MCC()))

    def get_roc_point(self):
        tpr = self.recall
        fpr = self.fpr
        if not tpr or not fpr:
            return [0,0]
        return [sum(fpr)/len(fpr),sum(tpr)/len(tpr)]

    def get_precision_summary(self):
        if not self.precision: return 0
        return  sum(self.precision)/len(self.precision)

    def get_f05_summary(self):
        if not self.f05: return 0
        return  sum(self.f05)/len(self.f05)

    def get_mcc_summary(self):
        if not self.mcc: return 0
        return  sum(self.mcc)/len(self.mcc)

if __name__ == '__main__':
    if len(sys.argv)<3:
        print "Usage: k-suite strategy_str sample_file"
        exit(1)
    threshold = 20
    iterations = 30
    neighbors = [3,5,10,50,100,150,200,300,400,500]
    cfg = Config()
    cfg.strategy = sys.argv[1]
    sample_file = sys.argv[2]
    population_sample = []
    with open(sample_file,'r') as f:
        for line in f.readlines():
            user_id = line.strip('\n')
            population_sample.append(os.path.join(cfg.popcon_dir,user_id[:2],user_id))
    # setup dictionaries and files
    roc_summary = {}
    recommended = {}
    precision_summary = {}
    f05_summary = {}
    mcc_summary = {}
    sample_dir = ("results/k-suite/%s" % sample_file.split('/')[-1])
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)
    log_file = os.path.join(sample_dir,cfg.strategy)
    with open(log_file,'w') as f:
        f.write("# %s\n\n" % sample_file.split('/')[-1])
        f.write("# strategy %s recommendation_size %d iterations %d\n\n" %
                (cfg.strategy,threshold,iterations))
        f.write("# k coverage \tprecision \tf05 \tmcc\n\n")

    for k in neighbors:
        roc_summary[k] = []
        recommended[k] = set()
        precision_summary[k] = []
        f05_summary[k] = []
        mcc_summary[k] = []
        with open(log_file+"-k%.3d"%k,'w') as f:
            f.write("# %s\n\n" % sample_file.split('/')[-1])
            f.write("# strategy-k %s-k%.3d\n\n" % (cfg.strategy,k))
            f.write("# roc_point \tprecision \tf05 \tmcc\n\n")

    # main loop per user
    for submission_file in population_sample:
        user = PopconSystem(submission_file)
        user.filter_pkg_profile(cfg.pkgs_filter)
        user.maximal_pkg_profile()
        for k in neighbors:
            cfg.k_neighbors = k
            rec = Recommender(cfg)
            repo_size = rec.items_repository.get_doccount()
            results = ExperimentResults(repo_size)
            # n iterations for same recommender and user
            for n in range(iterations):
                # Fill sample profile
                profile_len = len(user.pkg_profile)
                item_score = {}
                for pkg in user.pkg_profile:
                    item_score[pkg] = user.item_score[pkg]
                sample = {}
                sample_size = int(profile_len*0.9)
                for i in range(sample_size):
                     key = random.choice(item_score.keys())
                     sample[key] = item_score.pop(key)
                iteration_user = User(item_score)
                recommendation = rec.get_recommendation(iteration_user,threshold)
                if hasattr(recommendation,"ranking"):
                    results.add_result(recommendation.ranking,sample)
                    recommended[k] = recommended[k].union(recommendation.ranking)
            # save summary
            roc_point = results.get_roc_point()
            roc_summary[k].append(roc_point)
            precision = results.get_precision_summary()
            precision_summary[k].append(precision)
            f05 = results.get_f05_summary()
            f05_summary[k].append(f05)
            mcc = results.get_mcc_summary()
            mcc_summary[k].append(mcc)
            with open(log_file+"-k%.3d"%k,'a') as f:
                f.write("[%.2f,%.2f] \t%.4f \t%.4f \t%.4f\n" %
                        (roc_point[0],roc_point[1],precision,f05,mcc))
    # back to main flow
    with open(log_file,'a') as f:
        plot_summary(precision_summary,f05_summary,mcc_summary,log_file)
        for k in neighbors:
            coverage = len(recommended[size])/float(repo_size)
            f.write("%3d \t%.2f \t%.4f \t%.4f \t%.4f\n" %
                    (k,coverage,float(sum(precision_summary[k]))/len(precision_summary[k]),
                     float(sum(f05_summary[k]))/len(f05_summary[k]),
                     float(sum(mcc_summary[k]))/len(mcc_summary[k])))
            plot_roc(k,roc_summary[k],log_file)
