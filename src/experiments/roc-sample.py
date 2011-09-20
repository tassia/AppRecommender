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
import shutil

def plot_roc(results,log_file,mean=0):
    g = Gnuplot.Gnuplot()
    g('set style data lines')
    g.xlabel('False Positive Rate')
    g.ylabel('True Positive Rate')
    g('set xrange [0:1.0]')
    g('set yrange [0:1.0]')
    g.title("Setup: %s" % log_file.split("/")[-1])
    g('set label "C %.4f" at 0.68,0.2' % results.coverage())
    g('set label "AUC %.4f" at 0.68,0.15' % results.get_auc())
    g('set label "P(10) %.2f +- %.2f" at 0.68,0.10' % (numpy.mean(results.precision[10]),numpy.std(results.precision[10])))
    g('set label "F05(100) %.2f +- %.2f" at 0.68,0.05' % (numpy.mean(results.f05[100]),numpy.std(results.f05[100])))
    if mean==1:
        g.plot(Gnuplot.Data(results.get_roc_points(),title="mean ROC"),
               Gnuplot.Data([[0,0],[1,1]],with_="lines lt 7"))
        g.hardcopy(log_file+"-roc-mean.png",terminal="png")
        g.hardcopy(log_file+"-roc-mean.ps",terminal="postscript",enhanced=1,color=1)
    else:
        g.plot(Gnuplot.Data(results.get_roc_points(),title="ROC",with_="xyerrorbars"),
               Gnuplot.Data([[0,0],[1,1]],with_="lines lt 7"))
        g.hardcopy(log_file+"-roc.png",terminal="png")
        g.hardcopy(log_file+"-roc.ps",terminal="postscript",enhanced=1,color=1)

def get_label(cfg):
    label = {}
    if cfg.strategy in content_based:
        label["description"] = "strategy-profile"
        label["values"] = ("%s-profile%.3d" %
                           (cfg.strategy,cfg.profile_size))
    elif cfg.strategy in collaborative:
       label["description"] = "strategy-knn"
       label["values"] = ("%s-k%.3d" %
                          (cfg.strategy,cfg.k_neighbors))
    elif cfg.strategy in hybrid:
       label["description"] = "strategy-knn-profile"
       label["values"] = ("%s-k%.3d-profile%.3d" %
                          (cfg.strategy,cfg.k_neighbors,cfg.profile_size))
    return label

class ExperimentResults:
    def __init__(self,repo_size):
        self.repository_size = repo_size
        self.precision = {}
        self.recall = {}
        self.fpr = {}
        self.f05 = {}
        self.recommended = {}
        self.thresholds = [1]+range(10,self.repository_size,10)
        for size in self.thresholds:
            self.precision[size] = []
            self.recall[size] = []
            self.fpr[size] = []
            self.f05[size] = []
            self.recommended[size] = set()

    def add_result(self,ranking,sample):
        for size in self.thresholds:
            recommendation = ranking[:size]
            self.recommended[size] = self.recommended[size].union(recommendation)
            predicted = RecommendationResult(dict.fromkeys(recommendation,1))
            real = RecommendationResult(sample)
            evaluation = Evaluation(predicted,real,self.repository_size)
            self.precision[size].append(evaluation.run(Precision()))
            self.recall[size].append(evaluation.run(Recall()))
            self.f05[size].append(evaluation.run(F_score(0.5)))
            self.fpr[size].append(evaluation.run(FPR()))

    def precision_summary(self):
        return [[size,numpy.mean(self.precision[size])] for size in self.thresholds]

    def recall_summary(self):
        return [[size,numpy.mean(self.recall[size])] for size in self.thresholds]

    def f05_summary(self):
        return [[size,numpy.mean(self.f05[size])] for size in self.thresholds]

    def coverage_summary(self):
        return [[size,self.coverage(size)] for size in self.thresholds]

    def coverage(self,size=0):
        if not size:
            size = self.thresholds[-1]
        return len(self.recommended[size])/float(self.repository_size)

    def precision(self,size):
        return numpy.mean(results.precision[size])

    def get_auc(self):
        roc_points = self.get_roc_points()
        x_roc = [p[0] for p in roc_points]
        y_roc = [p[1] for p in roc_points]
        x_roc.insert(0,0)
        y_roc.insert(0,0)
        x_roc.append(1)
        y_roc.append(1)
        return numpy.trapz(y=y_roc, x=x_roc)

    # Average ROC by threshold (= size of recommendation)
    def get_roc_points(self):
        points = []
        for size in self.recall.keys():
            tpr = self.recall[size]
            fpr = self.fpr[size]
            points.append([numpy.mean(fpr),numpy.mean(tpr),numpy.std(fpr),numpy.std(tpr)])
        return sorted(points)

def run_strategy(cfg,sample_file):
    rec = Recommender(cfg)
    repo_size = rec.items_repository.get_doccount()
    results = ExperimentResults(repo_size)
    label = get_label(cfg)
    population_sample = []
    sample_str = sample_file.split('/')[-1]
    with open(sample_file,'r') as f:
        for line in f.readlines():
            user_id = line.strip('\n')
            population_sample.append(os.path.join(cfg.popcon_dir,user_id[:2],user_id))
    sample_dir = ("results/roc-sample/%s" % sample_str)
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)
    log_file = os.path.join(sample_dir,label["values"])

    # n iterations per population user
    for submission_file in population_sample:
        user = PopconSystem(submission_file)
        user.filter_pkg_profile(cfg.pkgs_filter)
        user.maximal_pkg_profile()
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
            recommendation = rec.get_recommendation(iteration_user,repo_size)
            if hasattr(recommendation,"ranking"):
                results.add_result(recommendation.ranking,sample)

    plot_roc(results,log_file)
    plot_roc(results,log_file,1)
    with open(log_file+"-roc.jpg.comment",'w') as f:
        f.write("# %s\n# %s\n\n" %
                (label["description"],label["values"]))
        f.write("# roc AUC\n%.4f\n\n"%results.get_auc())
        f.write("# threshold\tmean_fpr\tdev_fpr\t\tmean_tpr\tdev_tpr\t\tcoverage\n")
        for size in results.thresholds:
            f.write("%4d\t\t%.4f\t\t%.4f\t\t%.4f\t\t%.4f\t\t%.4f\n" %
                    (size,numpy.mean(results.fpr[size]),
                     numpy.std(results.fpr[size]),
                     numpy.mean(results.recall[size]),
                     numpy.std(results.recall[size]),
                     numpy.mean(results.coverage(size))))

def run_content(cfg,sample_file):
    for size in profile_size:
        cfg.profile_size = size
        run_strategy(cfg,sample_file)

def run_collaborative(cfg,sample_file):
    for k in neighbors:
        cfg.k_neighbors = k
        run_strategy(cfg,sample_file)

def run_hybrid(cfg,sample_file):
    for k in neighbors:
        cfg.k_neighbors = k
        for size in profile_size:
            cfg.profile_size = size
            run_strategy(cfg,sample_file)

if __name__ == '__main__':
    if len(sys.argv)<2:
        print "Usage: sample-roc strategy_str [popcon_sample_path]"
        exit(1)

    #iterations = 3
    #content_based = ['cb']
    #collaborative = ['knn_eset']
    #hybrid = ['knnco']
    #profile_size = [50,100]
    #neighbors = [50]
    iterations = 20
    content_based = ['cb','cbt','cbd','cbh','cb_eset','cbt_eset','cbd_eset','cbh_eset']
    collaborative = ['knn_eset','knn','knn_plus']
    hybrid = ['knnco','knnco_eset']
    profile_size = [10,20,50,100,200]
    neighbors = [200]
    #neighbors = [3,10,50,100,200]
    #profile_size = [10,20,40,60,80,100,140,170,200,240]
    #neighbors = [3,5,10,20,30,50,70,100,150,200]
    
    cfg = Config()
    cfg.strategy = sys.argv[1]
    sample_file = sys.argv[2]

    if cfg.strategy in content_based:
        run_content(cfg,sample_file)
    if cfg.strategy in collaborative:
        run_collaborative(cfg,sample_file)
    if cfg.strategy in hybrid:
        run_hybrid(cfg,sample_file)
