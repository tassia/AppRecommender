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

def plot_roc(p,roc_points,log_file):
    g = Gnuplot.Gnuplot()
    g('set style data points')
    g.xlabel('False Positive Rate')
    g.ylabel('True Positive Rate')
    g('set xrange [0:1.0]')
    g('set yrange [0:1.0]')
    g.title("Setup: %s" % log_file.split("/")[-1])
    g.plot(Gnuplot.Data([[0,0],[1,1]],with_="lines lt 7"),
           Gnuplot.Data(roc_points,title="k %d"%k))
    g.hardcopy(log_file+("-k%.3d.png"%k),terminal="png")
    g.hardcopy(log_file+("-k%.3d.ps"%k),terminal="postscript",enhanced=1,color=1)

class ExperimentResults:
    def __init__(self,repo_size):
        self.repository_size = repo_size
        self.precision = []
        self.recall = []
        self.fpr = []

    def add_result(self,ranking,sample):
        predicted = RecommendationResult(dict.fromkeys(ranking,1))
        real = RecommendationResult(sample)
        evaluation = Evaluation(predicted,real,self.repository_size)
        self.precision.append(evaluation.run(Precision()))
        self.recall.append(evaluation.run(Recall()))
        self.fpr.append(evaluation.run(FPR()))

    # Average ROC by threshold (whici is the size)
    def get_roc_point(self):
        tpr = self.recall
        fpr = self.fpr
        return [sum(fpr)/len(fpr),sum(tpr)/len(tpr)]

    def get_precision_summary(self):
        return  sum(self.precision)/len(self.precision)

    def get_recall_summary(self):
        return  sum(self.recall)/len(self.recall)

if __name__ == '__main__':
    # experiment parameters
    threshold = 20
    iterations = 30
    sample_file = "results/misc-popcon/sample-050-100"
    neighbors = [3,5,10,50,100,150,200,300,400,500]
    cfg = Config()
    cfg.strategy = "knn"
    print cfg.popcon_index
    sample = []
    with open(sample_file,'r') as f:
        for line in f.readlines():
            user_id = line.strip('\n')
            sample.append(os.path.join(cfg.popcon_dir,user_id[:2],user_id))
    # setup dictionaries and files
    roc_points = {}
    recommended = {}
    precisions = {}
    aucs = {}
    log_file = "results/k-suite/sample-050-100/%s" % (cfg.strategy)
    for k in neighbors:
        roc_points[k] = []
        recommended[k] = set()
        precisions[k] = []
        aucs[k] = []
        with open(log_file+"-k%.3d"%k,'w') as f:
            f.write("# strategy-k %s-k%.3d\n\n" % (cfg.strategy,k))
            f.write("# roc_point \tp(20) \tauc\n\n") 
    # main loop per user
    for submission_file in sample:
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
                profile_size = len(user.pkg_profile)
                item_score = {}
                for pkg in user.pkg_profile:
                    item_score[pkg] = user.item_score[pkg]
                sample = {}
                sample_size = int(profile_size*0.9)
                for i in range(sample_size):
                     key = random.choice(item_score.keys())
                     sample[key] = item_score.pop(key)
                iteration_user = User(item_score)
                recommendation = rec.get_recommendation(iteration_user,threshold)
                if hasattr(recommendation,"ranking"):
                    results.add_result(recommendation.ranking,sample)
                    print "ranking",recommendation.ranking
                    print "recommended_%d"%k,recommended[k]
                    recommended[k] = recommended[k].union(recommendation.ranking)
                    print recommended[k]
            # save summary
            roc_point = results.get_roc_point()
            auc = numpy.trapz(y=[0,roc_point[1],1],x=[0,roc_point[0],1])
            p_20 = results.get_precision_summary()
            roc_points[k].append(roc_point)
            aucs[k].append(auc)
            precisions[k].append(p_20)
            with open(log_file+"-k%.3d"%k,'a') as f:
                f.write("%s \t%.2f \t%.4f\n" % (str(roc_point),p_20,auc))
    # back to main flow
    with open(log_file,'w') as f:
        f.write("# k coverage \tp(20) \tauc\n\n")
        for k in neighbors:
            print "len_recommended_%d"%k,len(recommended[k])
            print "repo_size",repo_size
            coverage = len(recommended[k])/float(repo_size)
            print coverage
            f.write("%d \t%.2f \t%.2f \t%.2fi\n" %
                    (k,coverage,float(sum(precisions[k]))/len(precisions[k]),
                     float(sum(aucs[k]))/len(aucs[k])))
            plot_roc(k,roc_points[k],log_file)
