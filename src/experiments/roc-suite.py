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

#iterations = 3
#sample_proportions = [0.9]
#weighting = [('bm25',1.2)]
#collaborative = ['knn_eset']
#content_based = ['cb']
#hybrid = ['knnco']
#profile_size = [50,100]
#popcon_size = ["1000"]
#neighbors = [50]

iterations = 30
sample_proportions = [0.9]
weighting = [('bm25',1.0)]
content_based = ['cb','cbt','cbd','cbh','cb_eset','cbt_eset','cbd_eset','cbh_eset']
collaborative = ['knn_eset','knn','knn_plus']
hybrid = ['knnco','knnco_eset']
profile_size = range(20,200,40)
neighbors = range(10,510,50)

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

def plot_roc(roc_points,eauc,c,p,log_file):
    g = Gnuplot.Gnuplot()
    g('set style data lines')
    g.xlabel('False Positive Rate')
    g.ylabel('True Positive Rate')
    g('set xrange [0:1.0]')
    g('set yrange [0:1.0]')
    g.title("Setup: %s" % log_file.split("/")[-1])
    g('set label "C %.2f" at 0.8,0.25' % c)
    g('set label "P(20) %.2f" at 0.8,0.2' % p)
    g('set label "AUC %.4f" at 0.8,0.15' % eauc)
    g.plot(Gnuplot.Data(roc_points,title="ROC"),
           Gnuplot.Data([[0,0],[1,1]],with_="lines lt 7"))
           #Gnuplot.Data([roc_points[-1],[1,1]],with_="lines lt 6"))
    g.hardcopy(log_file+"-roc.png",terminal="png")
    g.hardcopy(log_file+"-roc.ps",terminal="postscript",enhanced=1,color=1)

def get_label(cfg,sample_proportion):
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
    else:
        print "Unknown strategy"
    return label

class ExperimentResults:
    def __init__(self,repo_size):
        self.repository_size = repo_size
        self.precision = {}
        self.recall = {}
        self.fpr = {}
        points = [1]+range(10,self.repository_size,10)
        self.recommended = set()
        for size in points:
            self.precision[size] = []
            self.recall[size] = []
            self.fpr[size] = []

    def add_result(self,ranking,sample):
        self.recommended = self.recommended.union(ranking)
        # get data only for point
        for size in self.precision.keys():
            predicted = RecommendationResult(dict.fromkeys(ranking[:size],1))
            real = RecommendationResult(sample)
            evaluation = Evaluation(predicted,real,self.repository_size)
            self.precision[size].append(evaluation.run(Precision()))
            self.recall[size].append(evaluation.run(Recall()))
            self.fpr[size].append(evaluation.run(FPR()))

    # Average ROC by threshold (= size of recommendation)
    def get_roc_points(self):
        points = []
        for size in self.recall.keys():
            tpr = self.recall[size]
            fpr = self.fpr[size]
            points.append([sum(fpr)/len(fpr),sum(tpr)/len(tpr)])
        return sorted(points)

def run_strategy(cfg,user):
    for weight in weighting:
        cfg.weight = weight[0]
        cfg.bm25_k1 = weight[1]
        rec = Recommender(cfg)
        repo_size = rec.items_repository.get_doccount()
        for proportion in sample_proportions:
            results = ExperimentResults(repo_size)
            label = get_label(cfg,proportion)
            user_dir = ("results/roc-suite/%s" % user.user_id[:8])
            if not os.path.exists(user_dir):
                os.mkdir(user_dir)
            log_file = os.path.join(user_dir,label["values"])
            for n in range(iterations):
                # Fill sample profile
                profile_len = len(user.pkg_profile)
                item_score = {}
                for pkg in user.pkg_profile:
                    item_score[pkg] = user.item_score[pkg]
                sample = {}
                sample_size = int(profile_len*proportion)
                for i in range(sample_size):
                     key = random.choice(item_score.keys())
                     sample[key] = item_score.pop(key)
                iteration_user = User(item_score)
                recommendation = rec.get_recommendation(iteration_user,repo_size)
                write_recall_log(label,n,sample,recommendation,profile_len,repo_size,log_file)
                if hasattr(recommendation,"ranking"):
                    results.add_result(recommendation.ranking,sample)
            with open(log_file,'w') as f:
                roc_points = results.get_roc_points()
                x_coord = [p[0] for p in roc_points]
                y_coord = [p[1] for p in roc_points]
                auc = numpy.trapz(y=y_coord, x=x_coord)
                eauc = (auc+
                        numpy.trapz(y=[0,roc_points[0][1]],x=[0,roc_points[0][0]])+
                        numpy.trapz(y=[roc_points[-1][1],1],x=[roc_points[-1][0],1]))
                precision_20 = sum(results.precision[10])/len(results.precision[10])
                coverage = len(results.recommended)/float(repo_size)
                f.write("# %s\n# %s\n\n" %
                        (label["description"],label["values"]))
                f.write("# coverage \tp(20) \tauc \teauc\n\t%.2f \t%.2f \t%.4f \t%.4f\n\n" %
                        (coverage,precision_20,auc,eauc))
            plot_roc(roc_points,eauc,coverage,precision_20,log_file)

def run_content(user,cfg):
    for strategy in content_based:
        cfg.strategy = strategy
        for size in profile_size:
            cfg.profile_size = size
            run_strategy(cfg,user)

def run_collaborative(user,cfg):
    popcon_desktopapps = cfg.popcon_desktopapps
    popcon_programs = cfg.popcon_programs
    for strategy in collaborative:
        cfg.strategy = strategy
        for k in neighbors:
            cfg.k_neighbors = k
            run_strategy(cfg,user)

def run_hybrid(user,cfg):
    popcon_desktopapps = cfg.popcon_desktopapps
    popcon_programs = cfg.popcon_programs
    for strategy in hybrid:
        cfg.strategy = strategy
        for k in neighbors:
            cfg.k_neighbors = k
            for size in profile_size:
                cfg.profile_size = size
                run_strategy(cfg,user)

if __name__ == '__main__':
    if len(sys.argv)<2:
        print "Usage: roc-suite popcon_submission_path [content|collaborative|hybrid]"
        exit(1)

    cfg = Config()
    user = PopconSystem(sys.argv[1])
    user.filter_pkg_profile(cfg.pkgs_filter)
    user.maximal_pkg_profile()

    if "content" in sys.argv or len(sys.argv)<3:
        run_content(user,cfg)
    if "collaborative" in sys.argv or len(sys.argv)<3:
        run_collaborative(user,cfg)
    if "hybrid" in sys.argv or len(sys.argv)<3:
        run_hybrid(user,cfg)
