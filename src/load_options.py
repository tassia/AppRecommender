#!/usr/bin/env python

import getopt
import os
import sys
import logging

from config import Config
from singleton import Singleton


class LoadOptions(Singleton):

    def __init__(self):
        self.options = []

    def load(self):
        config = Config()
        short_options = "hdvo:f:b:a:e:p:m:u:l:c:x:w:s:z:r:n:idvo:tdvo"
        long_options = ["help", "debug", "verbose", "output=", "filtersdir=",
                        "pkgsfilter=", "axi=", "dde=", "popconindex=",
                        "popcondir=", "indexmode=", "clustersdir=",
                        "kmedoids=", "maxpopcon=", "weight=", "strategy=",
                        "profile_size=", "profiling=", "neighbors=", "init",
                        "train"]
        try:
            opts, args = getopt.getopt(sys.argv[1:], short_options,
                                       long_options)
            self.options = opts
        except getopt.GetoptError as error:
            config.set_logger()
            logging.error("Bad syntax: %s" % str(error))
            self.usage()
            sys.exit()

        for o, p in opts:
            if o in ("-h", "--help"):
                self.usage()
                sys.exit()
            elif o in ("-d", "--debug"):
                config.debug = 1
            elif o in ("-v", "--verbose"):
                config.verbose = 1
            elif o in ("-o", "--output"):
                config.output = p
            elif o in ("-f", "--filtersdir"):
                config.filters_dir = p
            elif o in ("-b", "--pkgsfilter"):
                config.pkgs_filter = p
            elif o in ("-a", "--axi"):
                config.axi = p
            elif o in ("-e", "--dde"):
                config.dde_url = p
            elif o in ("-p", "--popconindex"):
                config.popcon_index = p
            elif o in ("-m", "--popcondir"):
                config.popcon_dir = p
            elif o in ("-u", "--index_mode"):
                config.index_mode = p
            elif o in ("-l", "--clustersdir"):
                config.clusters_dir = p
            elif o in ("-c", "--kmedoids"):
                config.k_medoids = int(p)
            elif o in ("-x", "--max_popcon"):
                config.max_popcon = int(p)
            elif o in ("-w", "--weight"):
                config.weight = p
            elif o in ("-s", "--strategy"):
                config.strategy = p
            elif o in ("-z", "--profile_size"):
                config.profile_size = int(p)
            elif o in ("-z", "--profiling"):
                config.profiling = p
            elif o in ("-n", "--neighbors"):
                config.k_neighbors = int(p)
            elif o in ("-i", "--init"):
                continue
            elif o in ("-t", "--train"):
                continue
            else:
                assert False, "unhandled option"

    def usage(self):
        """
        Print usage help.
        """
        print "[FIXME: deprecated help]"
        print "\n [ general ]"
        print "  -h, --help                 Print this help"
        print "  -i, --init                 Initialize AppRecommender data"
        print "  -t, --train                Make training of AppRecommender" \
              " machine learning"
        print "  -d, --debug                Set logging level to debug"
        print "  -v, --verbose              Set logging level to verbose"
        print "  -o, --output=PATH          Path to file to save output"
        print ""
        print " [ data sources ]"
        print "  -f, --filtersdir=PATH      Path to filters directory"
        print "  -b, --pkgsfilter=FILTER    File containing packages" \
              "to be considered for recommendations"
        print "  -a, --axi=PATH             Path to apt-xapian-index"
        print "  -p, --popconindex=PATH     Path to popcon index"
        print "  -e, --dde=URL              DDE url"

        # deprecated options
        # print " -m, --popcondir=PATH    Path to popcon submissions dir"
        # print " -u, --indexmode=MODE    " \
        #        "'old'|'reindex'|'cluster'|'recluster'"
        # print " -l, --clustersdir=PATH  Path to popcon clusters dir"
        # print " -c, --medoids=k         " \
        #        "Number of medoids for clustering"
        # print " -x, --maxpopcon=k       " \
        #        "Number of submissions to be considered"

        print ""
        print " [ recommender ]"
        print "  -w, --weight=OPTION        Search weighting scheme"
        print "  -s, --strategy=OPTION      Recommendation strategy"
        print "  -z, --profilesize=k        Size of user profile"
        print "  -r, --profiling=OPTION     Profile filter strategy"
        print "  -n, --neighbors=k          " \
              "Size of neighborhood for collaboration"
        print ""
        print " [ weight options ] "
        print "  trad = traditional probabilistic weighting"
        print "  bm25 = bm25 weighting scheme"
        print ""
        print " [ strategy options ] "
        print "  cb = content-based, mixed profile"
        print "  cbt = content-based, tags only profile"
        print "  cbd = content-based, description terms only profile"
        print "  cbh = content-based, half-half profile"
        print "  cbtm = content-based, time-context profile"
        print "  cb_eset = cb with eset profiling"
        print "  cbt_eset = cbt with eset profiling"
        print "  cbd_eset = cbd_eset with eset profiling"
        print "  cbh_eset = cbh with eset profiling"
        print "  knn = collaborative, tf-idf knn"
        print "  knn_plus = collaborative, tf-idf weighted knn"
        print "  knn_eset = collaborative, eset knn"
        print "  knnco = collaborative through content"
        print "  knnco_eset = collaborative through content," \
              " eset recommendation"
        print "  mlbva = machine_learning, Binary Vector Approach"
        print "  mlbow = machine_learning, Bag Of Words"
        print ""
        print " [ to train machine learning ] "
        print "  on path '/bin' run the script" \
              " 'apprec_ml_traning.py'"
