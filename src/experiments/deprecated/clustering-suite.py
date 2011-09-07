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
import os
sys.path.insert(0,'../')
from config import Config
from data import PopconXapianIndex, PopconSubmission
from recommender import Recommender
from user import LocalSystem, User
from evaluation import *
import logging
import random
import Gnuplot

if __name__ == '__main__':

    cfg = Config()
    cfg.index_mode = "recluster"
    logging.info("Starting clustering experiments")
    logging.info("Medoids: %d\t Max popcon:%d" % (cfg.k_medoids,cfg.max_popcon))
    cfg.popcon_dir = os.path.expanduser("~/org/popcon.debian.org/popcon-mail/popcon-entries/")
    cfg.popcon_index = cfg.popcon_index+("_%dmedoids%dmax" %
                                         (cfg.k_medoids,cfg.max_popcon))
    cfg.clusters_dir = cfg.clusters_dir+("_%dmedoids%dmax" %
                                         (cfg.k_medoids,cfg.max_popcon))
    pxi = PopconXapianIndex(cfg)
    logging.info("Overall dispersion: %f\n" % pxi.cluster_dispersion)
    # Write clustering log
    output = open(("results/clustering/%dmedoids%dmax" % (cfg.k_medoids,cfg.max_popcon)),'w')
    output.write("# k_medoids\tmax_popcon\tdispersion\n")
    output.write("%d %f\n" % (cfg.k_medoids,cfg.max_popcon,pxi.cluster_dispersion))
    output.close()
