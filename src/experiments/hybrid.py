#!/usr/bin/env python
"""
    hybrid-suite
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

#hybrid_strategies = ['knnco','knnco_eset']

if __name__ == '__main__':
    if len(sys.argv)<2:
        print "Usage: hybrid strategy sample_file"
        exit(1)

    iterations = 20
    profile_size = [10,40,70,100,170,240]
    neighbor_size = [3,10,50,70,100,150,200]

    #iterations = 1
    #profile_size = [10,20,30]
    #neighbor_size = [10,20,30]

    cfg = Config()
    population_sample = []
    strategy = sys.argv[1]
    sample_file = sys.argv[2]
    sample_str = sample_file.split('/')[-1]
    with open(sample_file,'r') as f:
        for line in f.readlines():
            user_id = line.strip('\n')
            population_sample.append(os.path.join(cfg.popcon_dir,user_id[:2],user_id))
    sample_dir = ("results/hybrid/%s/%s" % (sample_str,strategy))
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)

    cfg.strategy = strategy
    p_10_summary = {}
    f05_100_summary = {}
    c_10 = {}
    c_100 = {}

    log_file = os.path.join(sample_dir,sample_str+"-"+cfg.strategy)
    graph_10 = {}
    graph_100 = {}
    graph_10_jpg = {}
    graph_100_jpg = {}
    comment_10 = {}
    comment_100 = {}
    for k in neighbor_size:
        graph_10[k] = log_file+("-neighborhood%.3d-010.png"%k)
        graph_100[k] = log_file+("-neighborhood%.3d-100.png"%k)
        graph_10_jpg[k] = graph_10[k].strip(".png")+".jpg"
        graph_100_jpg[k] = graph_100[k].strip(".png")+".jpg"
        comment_10[k] = graph_10_jpg[k]+".comment"
        comment_100[k] = graph_100_jpg[k]+".comment"

        with open(comment_10[k],'w') as f:
            f.write("# %s\n" % sample_str)
            f.write("# strategy %s\n# threshold 10\n# iterations %d\n\n" %
                    (cfg.strategy,iterations))
            f.write("# neighborhood\tprofile\tmean_p_10\tdev_p_10\tc_10\n\n")
        with open(comment_100[k],'w') as f:
            f.write("# %s\n" % sample_str)
            f.write("# strategy %s\n# threshold 100\n# iterations %d\n\n" %
                    (cfg.strategy,iterations))
            f.write("# neighborhood\tprofile\tmean_f05_100\tdev_f05_100\tc_100\n\n")

        c_10[k] = {}
        c_100[k] = {}
        p_10_summary[k] = {}
        f05_100_summary[k] = {}
        for size in profile_size:
            c_10[k][size] = set()
            c_100[k][size] = set()
            p_10_summary[k][size] = []
            f05_100_summary[k][size] = []
            with open(log_file+"-neighborhood%.3d-profile%.3d"%(k,size),'w') as f:
                f.write("# %s\n" % sample_str)
                f.write("# strategy %s-neighborhood%.3d-profile%.3d\n\n" % (cfg.strategy,k,size))
                f.write("# p_10\t\tf05_100\n\n")

    # main loop per user
    for submission_file in population_sample:
        user = PopconSystem(submission_file)
        user.filter_pkg_profile(cfg.pkgs_filter)
        user.maximal_pkg_profile()
        for k in neighbor_size:
            cfg.k_neighbors = k
            for size in profile_size:
                cfg.profile_size = size
                rec = Recommender(cfg)
                repo_size = rec.items_repository.get_doccount()
                p_10 = []
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
                        predicted_10 = RecommendationResult(dict.fromkeys(ranking[:10],1))
                        evaluation = Evaluation(predicted_10,real,repo_size)
                        p_10.append(evaluation.run(Precision()))
                        predicted_100 = RecommendationResult(dict.fromkeys(ranking[:100],1))
                        evaluation = Evaluation(predicted_100,real,repo_size)
                        f05_100.append(evaluation.run(F_score(0.5)))
                        c_10[k][size] = c_10[k][size].union(recommendation.ranking[:10])
                        c_100[k][size] = c_100[k][size].union(recommendation.ranking[:100])
                # save summary
                if p_10:
                    p_10_summary[k][size].append(numpy.mean(p_10))
                if f05_100:
                    f05_100_summary[k][size].append(numpy.mean(f05_100))

                with open(log_file+"-neighborhood%.3d-profile%.3d"%(k,size),'a') as f:
                    f.write("%.4f\t\t%.4f\n" %
                            (numpy.mean(p_10),numpy.mean(f05_100)))

    # back to main flow
    coverage_10 = {}
    coverage_100 = {}
    for k in neighbor_size:
        coverage_10[k] = {}
        coverage_100[k] = {}
        with open(comment_10[k],'a') as f:
            for size in profile_size:
                coverage_10[k][size] = len(c_10[k][size])/float(repo_size)
                f.write("%3d\t\t%3d\t\t%.4f\t%.4f\t%.4f\n" %
                        (k,size,numpy.mean(p_10_summary[k][size]),
                         numpy.std(p_10_summary[k][size]),coverage_10[k][size]))
        with open(comment_100[k],'a') as f:
            for size in profile_size:
                coverage_100[k][size] = len(c_100[k][size])/float(repo_size)
                f.write("%3d\t\t%3d\t\t%.4f\t%.4f\t%.4f\n" %
                        (k,size,numpy.mean(f05_100_summary[k][size]),
                         numpy.std(f05_100_summary[k][size]),coverage_100[k][size]))

    for k in neighbor_size:
        # plot results summary
        g = Gnuplot.Gnuplot()
        g('set style data lines')
        g('set yrange [0:1.0]')
        g.xlabel('Profile size')
        g.title("Setup: %s-neighborhood%3d (threshold 10)" % (cfg.strategy,k))
        g.plot(Gnuplot.Data(sorted([[i,numpy.mean(p_10_summary[k][i]),numpy.std(p_10_summary[k][i])]
                                    for i in p_10_summary[k].keys()]),title="Precision"),
               Gnuplot.Data(sorted([[i,numpy.mean(p_10_summary[k][i]),numpy.std(p_10_summary[k][i])]
                                    for i in p_10_summary[k].keys()]),title="Deviation",
                                    with_="yerrorbar lt 2 pt 6"),
               Gnuplot.Data(sorted([[i,coverage_10[k][i]]
                                    for i in coverage_10[k].keys()]),title="Coverage"))
        g.hardcopy(graph_10[k],terminal="png")

        g = Gnuplot.Gnuplot()
        g('set style data lines')
        g('set yrange [0:1.0]')
        g.xlabel('Profile size')
        g.title("Setup: %s-neighborhood%3d (threshold 100)" % (cfg.strategy,k))
        g.plot(Gnuplot.Data(sorted([[i,numpy.mean(f05_100_summary[k][i]),numpy.std(f05_100_summary[k][i])]
                                    for i in f05_100_summary[k].keys()]),title="F05"),
               Gnuplot.Data(sorted([[i,numpy.mean(f05_100_summary[k][i]),numpy.std(f05_100_summary[k][i])]
                                    for i in f05_100_summary[k].keys()]),title="Deviation",
                                    with_="yerrorbar lt 2 pt 6"),
               Gnuplot.Data(sorted([[i,coverage_100[k][i]]
                                    for i in coverage_100[k].keys()]),title="Coverage"))
        g.hardcopy(graph_100[k],terminal="png")
