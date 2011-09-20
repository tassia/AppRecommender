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

def write_recall_log(label,n,sample,recommendation,profile_size,repo_size,log_file):
    # Write recall log
    output = open(("%s-%.2d" % (log_file,n)),'w')
    output.write("# %s-n\n" % label["description"])
    output.write("# %s-%.2d\n" % (label["values"],n))
    output.write("\n# repository profile sample\n%d %d %d\n" % \
                 (repo_size,profile_size,len(sample)))
    if hasattr(recommendation,"ranking"):
        notfound = []
        ranks = []
        for pkg in sample.keys():
            if pkg in recommendation.ranking:
                ranks.append(recommendation.ranking.index(pkg))
            else:
                notfound.append(pkg)
        for r in sorted(ranks):
            output.write(str(r)+"\n")
        if notfound:
            output.write("# out of recommendation:\n")
            for pkg in notfound:
                output.write(pkg+"\n")
    output.close()

def plot_summary(results,log_file):
    # Plot metrics summary
    g = Gnuplot.Gnuplot()
    g('set style data lines')
    g('set yrange [0:1.0]')
    g.xlabel('Threshold (recommendation size)')
    g.title("Setup: %s" % log_file.split("/")[-1])
    g.plot(Gnuplot.Data(results.precision_summary(),title="Precision"),
           Gnuplot.Data(results.recall_summary(),title="Recall"),
           Gnuplot.Data(results.f05_summary(),title="F05"),
           Gnuplot.Data(results.coverage_summary(),title="Coverage"))
    g.hardcopy(log_file+".png",terminal="png")
    g.hardcopy(log_file+".ps",terminal="postscript",enhanced=1,color=1)
    g('set logscale x')
    g('replot')
    g.hardcopy(log_file+"-logscale.png",terminal="png")
    g.hardcopy(log_file+"-logscale.ps",terminal="postscript",enhanced=1,color=1)

def plot_roc(results,log_file):
    g = Gnuplot.Gnuplot()
    g('set style data lines')
    g.xlabel('False Positive Rate')
    g.ylabel('True Positive Rate')
    g('set xrange [0:1.0]')
    g('set yrange [0:1.0]')
    g.title("Setup: %s" % log_file.split("/")[-1])
    g('set label "C %.2f" at 0.8,0.25' % results.coverage())
    g('set label "AUC %.2f" at 0.8,0.2' % results.get_auc())
    g('set label "P(10) %.2f" at 0.8,0.15' % numpy.mean(results.precision[10]))
    g('set label "P(20) %.2f" at 0.8,0.10' % numpy.mean(results.precision[20]))
    g('set label "F05(100) %.2f" at 0.8,0.05' % numpy.mean(results.f05[100]))
    g.plot(Gnuplot.Data(results.get_roc_points(),title="ROC"),
           Gnuplot.Data([[0,0],[1,1]],with_="lines lt 7"))
           #Gnuplot.Data([roc_points[-1],[1,1]],with_="lines lt 6"))
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
            print evaluation.run(Precision())
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
            points.append([sum(fpr)/len(fpr),sum(tpr)/len(tpr)])
        return sorted(points)

def run_strategy(cfg,user):
    rec = Recommender(cfg)
    repo_size = rec.items_repository.get_doccount()
    results = ExperimentResults(repo_size)
    label = get_label(cfg)
    user_dir = ("results/roc-suite/%s/%s" % (user.user_id[:8],cfg.strategy))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    log_file = os.path.join(user_dir,label["values"])
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
        write_recall_log(label,n,sample,recommendation,profile_len,repo_size,log_file)
        if hasattr(recommendation,"ranking"):
            results.add_result(recommendation.ranking,sample)
    with open(log_file+"-roc.jpg.comment",'w') as f:
        f.write("# %s\n# %s\n\n" %
                (label["description"],label["values"]))
        f.write("# roc AUC\n%.4f\n\n"%results.get_auc())
        f.write("# threshold\tprecision\trecall\t\tf05\t\tcoverage\n")
        for size in results.thresholds:
            f.write("%4d\t\t%.4f\t\t%.4f\t\t%.4f\t\t%.4f\n" %
                    (size,numpy.mean(results.precision[size]),
                     numpy.mean(results.recall[size]),
                     numpy.mean(results.f05[size]),
                     numpy.mean(results.coverage(size))))
    shutil.copy(log_file+"-roc.jpg.comment",log_file+".jpg.comment")
    shutil.copy(log_file+"-roc.jpg.comment",log_file+"-logscale.jpg.comment")
    plot_roc(results,log_file)
    plot_summary(results,log_file)

def run_content(user,cfg):
    for size in profile_size:
        cfg.profile_size = size
        run_strategy(cfg,user)

def run_collaborative(user,cfg):
    for k in neighbors:
        cfg.k_neighbors = k
        run_strategy(cfg,user)

def run_hybrid(user,cfg):
    for k in neighbors:
        cfg.k_neighbors = k
        for size in profile_size:
            cfg.profile_size = size
            run_strategy(cfg,user)

if __name__ == '__main__':
    if len(sys.argv)<2:
        print "Usage: roc-suite strategy_str [popcon_submission_path]"
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
    profile_size = [10,20,40,60,80,100,140,170,200,240]
    neighbors = [3,5,10,20,30,50,70,100,150,200]
    
    cfg = Config()
    cfg.strategy = sys.argv[1]

    #user = PopconSystem("/root/.app-recommender/popcon-entries/4a/4a67a295ec14826db2aa1d90be2f1623")
    user = PopconSystem("/root/.app-recommender/popcon-entries/8b/8b44fcdbcf676e711a153d5db09979d7")
    #user = PopconSystem(sys.argv[1])
    user.filter_pkg_profile(cfg.pkgs_filter)
    user.maximal_pkg_profile()

    if cfg.strategy in content_based:
        run_content(user,cfg)
    if cfg.strategy in collaborative:
        run_collaborative(user,cfg)
    if cfg.strategy in hybrid:
        run_hybrid(user,cfg)
