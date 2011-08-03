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

def run_iteration(label,cfg,sample_proportion,n):
    rec = Recommender(cfg)
    repo_size = rec.items_repository.get_doccount()
    user = RandomPopcon(cfg.popcon_dir,os.path.join(cfg.filters,"desktop"))
    print "profile",user.pkg_profile
    user.maximal_pkg_profile()
    sample_size = int(len(user.pkg_profile)*sample_proportion)
    for n in range(iteration):
        item_score = dict.fromkeys(user.pkg_profile,1)
        # Prepare partition
        sample = {}
        for i in range(sample_size):
             key = random.choice(item_score.keys())
             sample[key] = item_score.pop(key)
        # Get full recommendation
        user = User(item_score)
        recommendation = rec.get_recommendation(user,repo_size)
        # Write recall log
        log_file = "results/strategies/"+label["values"]
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
        g.hardcopy(log_file+"-plot.ps", enhanced=1, color=1)


if __name__ == '__main__':
    iteration = 10
    samples_proportion = [0.5, 0.6, 0.7, 0.8, 0.9]
    weights = ['bm25', 'trad']
    cb_strategies = ['cb','cbt','cbd']
    #cb_strategies = []
    profile_size = range(10,100,10)
    items_repository = ["data/AppAxi","/var/lib/apt-xapian-index/index"]
    users_repository = ["data/popcon_index_full","data/popcon_index-50000",
                        "data/popcon_index_10000","data/popcon_index_1000"]
    users_repository = []
    neighbors = range(10,1010,100)

    cfg = Config()
    cfg.index_mode = "old"
    label = {}

    for w in weights:
        cfg.weight = w
        for items_repo in items_repository:
            cfg.axi = items_repo
            if "App" in cfg.axi:
                axi_str = "axiapp"
            else:
                axi_str = "axifull"
            for sample_proportion in samples_proportion:
                if "content" in sys.argv or len(sys.argv)<2:
                    for size in profile_size:
                        cfg.profile_size = size
                        for strategy in cb_strategies:
                            cfg.strategy = strategy
                            for n in range(iteration):
                                label["description"] = "weight-axi-profile-strategy-sample-n"
                                label["values"] = ("%s-%s-%d-%s-%.2f-%d" %
                                                   (cfg.weight,axi_str,cfg.profile_size,
                                                    cfg.strategy,sample_proportion,n))
                                run_iteration(label,cfg,sample_proportion,n)
                if "colaborative" in sys.argv or len(sys.argv)<2:
                    cfg.strategy = "col"
                    for users_repo in users_repository:
                        cfg.popcon_index = users_repo
                        for k in neighbors:
                            cfg.k_neighbors = k
                            for n in range(iteration):
                                k_str = "k"+str(cfg.k_neighbors)
                                if "full" in cfg.popcon_index:
                                    popcon_str = "popfull"
                                if "50000" in cfg.popcon_index:
                                    popcon_str = "pop50000"
                                if "10000" in cfg.popcon_index:
                                    popcon_str = "pop10000"
                                if "1000" in cfg.popcon_index:
                                    popcon_str = "pop1000"
                                label["description"] = "weight-axi-popcon-profile-strategy-k-sample-n"
                                label["values"] = ("%s-%s-%s-%d-%s-%s-%.2f-%d" %
                                                   (cfg.weight,axi_str,popcon_str,cfg.profile_size,
                                                    cfg.strategy,k_str,sample_proportion,n))
                                run_iteration(label,cfg,sample_proportion,n)
