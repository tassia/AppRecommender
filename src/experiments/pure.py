#!/usr/bin/env python
"""
    profile-suite - experiment different profile sizes
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

if __name__ == '__main__':
    if len(sys.argv)<2:
        print "Usage: profile-suite strategy_category sample_file"
        exit(1)

    iterations = 20
    profile_size = [10,20,40,70,100,140,170,200,240]
    neighbor_size = [3,5,10,50,100,150,200,300,400,500]

    content_strategies = ['cb','cbt','cbd','cbh','cb_eset','cbt_eset','cbd_eset','cbh_eset']
    collaborative_strategies = ['knn_eset']#,'knn_eset','knn_plus']
    #collaborative_strategies = ['knn','knn_eset','knn_plus']

    #iterations = 1
    #profile_size = [10,20,30]
    #neighbor_size = [10,20,30]
    #content_strategies = ['cb']
    #collaborative_strategies = ['knn_eset']

    strategy_category = sys.argv[1]
    if strategy_category == "content":
        strategies = content_strategies
        sizes = profile_size
        option_str = "profile"
    elif strategy_category == "collaborative":
        strategies = collaborative_strategies
        sizes = neighbor_size
        option_str = "neighborhood"
    else:
        print "Usage: profile-suite strategy_category sample_file"
        exit(1)

    cfg = Config()
    population_sample = []
    sample_file = sys.argv[2]
    sample_str = sample_file.split('/')[-1]
    with open(sample_file,'r') as f:
        for line in f.readlines():
            user_id = line.strip('\n')
            population_sample.append(os.path.join(cfg.popcon_dir,user_id[:2],user_id))
    sample_dir = ("results/%s/%s" %
                  (strategy_category,sample_str))
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)

    for strategy in strategies:
        cfg.strategy = strategy
        p_20_summary = {}
        f05_100_summary = {}
        c_20 = {}
        c_100 = {}

        log_file = os.path.join(sample_dir,sample_str+"-"+cfg.strategy)
        graph_20 = log_file+"-20.png"
        graph_100 = log_file+"-100.png"
        graph_20_jpg = graph_20.strip(".png")+".jpg"
        graph_100_jpg = graph_100.strip(".png")+".jpg"
        comment_20 = graph_20_jpg+".comment"
        comment_100 = graph_100_jpg+".comment"

        with open(comment_20,'w') as f:
            f.write("# sample %s\n" % sample_str)
            f.write("# strategy %s\n# threshold 20\n# iterations %d\n\n" %
                    (cfg.strategy,iterations))
            f.write("# %s\tp_20\tc_20\n\n"%option_str)
        with open(comment_100,'w') as f:
            f.write("# sample %s\n" % sample_str)
            f.write("# strategy %s\n# threshold 100\n# iterations %d\n\n" %
                    (cfg.strategy,iterations))
            f.write("# %s\t\tf05_100\t\tc_100\n\n"%option_str)

        for size in sizes:
            c_20[size] = set()
            c_100[size] = set()
            p_20_summary[size] = []
            f05_100_summary[size] = []
            with open(log_file+"-%s%.3d"%(option_str,size),'w') as f:
                f.write("# sample %s\n" % sample_str)
                f.write("# strategy %s-%s%.3d\n\n" % (cfg.strategy,option_str,size))
                f.write("# p_20\tf05_100\n\n")

        # main loop per user
        for submission_file in population_sample:
            user = PopconSystem(submission_file)
            user.filter_pkg_profile(cfg.pkgs_filter)
            user.maximal_pkg_profile()
            for size in sizes:
                cfg.profile_size = size
                cfg.k_neighbors = size
                rec = Recommender(cfg)
                repo_size = rec.items_repository.get_doccount()
                p_20 = []
                f05_100 = []
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
                        ranking = recommendation.ranking
                        real = RecommendationResult(sample)
                        predicted_20 = RecommendationResult(dict.fromkeys(ranking[:20],1))
                        evaluation = Evaluation(predicted_20,real,repo_size)
                        p_20.append(evaluation.run(Precision()))
                        predicted_100 = RecommendationResult(dict.fromkeys(ranking[:100],1))
                        evaluation = Evaluation(predicted_100,real,repo_size)
                        f05_100.append(evaluation.run(F_score(0.5)))
                        c_20[size] = c_20[size].union(recommendation.ranking[:20])
                        c_100[size] = c_100[size].union(recommendation.ranking[:100])
                # save summary
                if p_20:
                    p_20_summary[size].append(sum(p_20)/len(p_20))
                if f05_100:
                    f05_100_summary[size].append(sum(f05_100)/len(f05_100))

                with open(log_file+"-%s%.3d"%(option_str,size),'a') as f:
                    f.write("%.4f \t%.4f\n" %
                            ((sum(p_20)/len(p_20),sum(f05_100)/len(f05_100))))

        # back to main flow
        coverage_20 = {}
        coverage_100 = {}
        with open(comment_20,'a') as f:
            for size in sizes:
                coverage_20[size] = len(c_20[size])/float(repo_size)
                f.write("%3d\t\t%.4f\t\t%.4f\n" %
                        (size,float(sum(p_20_summary[size]))/len(p_20_summary[size]),coverage_20[size]))
        with open(comment_100,'a') as f:
            for size in sizes:
                coverage_100[size] = len(c_100[size])/float(repo_size)
                f.write("%3d\t\t%.4f\t\t%.4f\n" %
                        (size,float(sum(f05_100_summary[size]))/len(f05_100_summary[size]),coverage_100[size]))

        # plot results summary
        g = Gnuplot.Gnuplot()
        g('set style data lines')
        g('set yrange [0:1.0]')
        g.xlabel('%s size'%option_str.capitalize())
        g.title("Setup: %s (threshold 20)" % cfg.strategy)
        g.plot(Gnuplot.Data(sorted([[k,sum(p_20_summary[k])/len(p_20_summary[k])]
                                    for k in p_20_summary.keys()]),title="Precision"),
               Gnuplot.Data(sorted([[k,coverage_20[k]]
                                    for k in coverage_20.keys()]),title="Coverage"))
        g.hardcopy(graph_20,terminal="png")
        commands.getoutput("convert -quality 20 %s %s" %
                           (graph_100,graph_20_jpg))
        g = Gnuplot.Gnuplot()
        g('set style data lines')
        g('set yrange [0:1.0]')
        g.xlabel('%s size'%option_str.capitalize())
        g.title("Setup: %s (threshold 100)" % cfg.strategy)
        g.plot(Gnuplot.Data(sorted([[k,sum(f05_100_summary[k])/len(f05_100_summary[k])]
                                    for k in f05_100_summary.keys()]),title="F05"),
               Gnuplot.Data(sorted([[k,coverage_100[k]]
                                    for k in coverage_100.keys()]),title="Coverage"))
        g.hardcopy(graph_100,terminal="png")
        commands.getoutput("convert -quality 100 %s %s" %
                           (graph_100,graph_100_jpg))
