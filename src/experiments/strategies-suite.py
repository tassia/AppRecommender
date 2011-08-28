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
from data import PopconXapianIndex, PopconSubmission, AppAptXapianIndex
from recommender import Recommender
from user import LocalSystem, User
from evaluation import *
import logging
import random
import Gnuplot

def write_recall_log(label,sample,recommendation,log_file):
    # Write recall log
    output = open(log_file,'w')
    output.write("# %s\n" % label["description"])
    output.write("# %s\n" % label["values"])
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
        output.write("Out of recommendation:\n")
        for pkg in notfound:
            output.write(pkg+"\n")
    output.close()

def plot_summary(sample,recommendation,repo_size,log_file):
    # Plot metrics summary
    accuracy = []
    precision = []
    recall = []
    f1 = []
    g = Gnuplot.Gnuplot()
    g('set style data lines')
    g.xlabel('Recommendation size')
    for size in range(1,len(recommendation.ranking)+1,100):
        predicted = RecommendationResult(dict.fromkeys(recommendation.ranking[:size],1))
        real = RecommendationResult(sample)
        evaluation = Evaluation(predicted,real,repo_size)
        accuracy.append([size,evaluation.run(Accuracy())])
        precision.append([size,evaluation.run(Precision())])
        recall.append([size,evaluation.run(Recall())])
        f1.append([size,evaluation.run(F1())])

    g.plot(Gnuplot.Data(accuracy,title="Accuracy"),
           Gnuplot.Data(precision,title="Precision"),
           Gnuplot.Data(recall,title="Recall"),
           Gnuplot.Data(f1,title="F1"))
    g.hardcopy(log_file+"-plot.ps", terminal="postscript")
    g.hardcopy(log_file+"-plot.ps", terminal="postscript")

def run_iteration(user,cfg,label,sample):
    rec = Recommender(cfg)
    repo_size = rec.items_repository.get_doccount()
    recommendation = rec.get_recommendation(user,repo_size)
    log_file = "results/strategies/"+label["values"]
    write_recall_log(label,sample,recommendation,log_file)
    plot_summary(sample,recommendation,repo_size,log_file)

def run_strategies(user,sample,n):
    cfg = Config()
    label = {}
    sample_proportion = (len(sample)/len(user.pkg_profile)+len(sample))
    for k in bm25_k1:
        cfg.bm25_k1 = k
        if "content" in sys.argv or len(sys.argv)<2:
            for size in profile_size:
                cfg.profile_size = size
                for strategy in content_based:
                    cfg.strategy = strategy
                    label["description"] = "k1_bm25-profile-strategy-sample-n"
                    label["values"] = ("%.2f-%d-%s-%.2f-%d" %
                                       (cfg.bm25_k1,cfg.profile_size,
                                        cfg.strategy,sample_proportion,n))
                    run_iteration(user,cfg,label,sample)
        if "colaborative" in sys.argv or len(sys.argv)<2:
            for strategy in collaborative:
                cfg.strategy = strategy
                for size in popcon_size:
                    cfg.popcon_desktopapps = cfg.popcon_desktopapps+size
                    cfg.popcon_programs = cfg.popcon_programs+size
                    for k in neighbors:
                        cfg.k_neighbors = k
                        k_str = "k"+str(cfg.k_neighbors)
                        label["description"] = "k1_bm25-popcon-strategy-k-sample-n"
                        label["values"] = ("%.2f-%s-%s-%s-%.2f-%d" %
                                           (cfg.bm25_k1,str(popcon_size),cfg.strategy,
                                            k_str,sample_proportion,n))
                        run_iteration(user,cfg,label,sample)

if __name__ == '__main__':
    iterations = 10
    samples_proportion = [0.5, 0.6, 0.7, 0.8, 0.9]
    weights = ['bm25', 'trad']
    bm25_k1 = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    content_based = ['cb','cbt','cbd','cbh',
                     'cb_eset','cbt_eset','cbd_eset','cbh_eset']
    collaborative = ['knn','knn_plus','knn_eset']
    hybrid = ['knnco','knnco_eset']

    profile_size = range(10,100,10)
    popcon_size = [1000,10000,50000,'full']
    neighbors = range(10,510,100)

    user = LocalSystem()
    #user = RandomPopcon(cfg.popcon_dir,os.path.join(cfg.filters_dir,"desktopapps"))
    user.maximal_pkg_profile()
    for sample_proportion in samples_proportion:
        for n in range(iterations):
            # Fill user profile
            item_score = {}
            for pkg in user.pkg_profile:
                item_score[pkg] = user.item_score[pkg]
            # Prepare partition sample
            sample = {}
            sample_size = int(len(user.pkg_profile)*sample_proportion)
            for i in range(sample_size):
                 key = random.choice(item_score.keys())
                 sample[key] = item_score.pop(key)
            run_strategies(User(item_score),sample,n)
