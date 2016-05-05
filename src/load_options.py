#!/usr/bin/env python

import getopt
import os
import sys
import logging

from config import Config
from ConfigParser import ConfigParser, MissingSectionHeaderError


class LoadOptions:

    def __init__(self):
        self.options = []
        self.config = Config()
        try:
            self.config_parser = ConfigParser()
            self.config_parser.read(['/etc/apprecommender/recommender.conf',
                              os.path.expanduser('~/.app_recommender.rc'),
                              os.path.expanduser('app_recommender.cfg')])
        except (MissingSectionHeaderError), err:
            logging.error("Error in config file syntax: %s", str(err))
            os.abort()

    def usage(self):
        """
        Print usage help.
        """
        print "[FIXME: deprecated help]"
        print "\n [ general ]"
        print "  -h, --help                 Print this help"
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

    def read_option(self, section, option):
        """
        Read option from configuration file if it is defined there or return
        default value.
        """
        var = "self.config.%s" % option
        if self.config_parser.has_option(section, option):
            return self.config_parser.get(section, option)
        else:
            return eval(var)

    def load(self):
        """
        Load options from configuration file and command line arguments.
        """
        self.config.debug = int(self.read_option('general', 'debug'))
        self.config.debug = int(self.read_option('general', 'verbose'))
        self.config.base_dir = os.path.expanduser(self.read_option('data_sources',
                                           'base_dir'))
        self.config.user_data_dir = os.path.join(self.config.base_dir,
                                          self.read_option('data_sources',
                                                           'user_data_dir'))
        self.config.output = os.path.join(self.config.base_dir,
                                   self.read_option('general', 'output'))
        self.config.filters_dir = os.path.join(self.config.base_dir,
                                        self.read_option('data_sources',
                                                         'filters_dir'))
        self.config.pkgs_filter = os.path.join(self.config.filters_dir,
                                        self.read_option('data_sources',
                                                         'pkgs_filter'))
        self.config.axi = self.read_option('data_sources', 'axi')
        self.config.axi_programs = os.path.join(self.config.base_dir,
                                         self.read_option('data_sources',
                                                          'axi_programs'))
        self.config.axi_desktopapps = os.path.join(self.config.base_dir,
                                            self.read_option(
                                                'data_sources',
                                                'axi_desktopapps'))
        # self.config.index_mode = self.read_option('data_sources', 'index_mode')
        self.config.popcon = int(self.read_option('data_sources', 'popcon'))
        self.config.popcon_programs = os.path.join(self.config.base_dir,
                                            self.read_option(
                                                'data_sources',
                                                'popcon_programs'))
        self.config.popcon_desktopapps = os.path.join(self.config.base_dir,
                                               self.read_option(
                                                   'data_sources',
                                                   'popcon_desktopapps'))
        self.config.popcon_index = os.path.join(self.config.base_dir,
                                         self.read_option('data_sources',
                                                          'popcon_index'))
        self.config.popcon_dir = os.path.join(self.config.base_dir,
                                       self.read_option('data_sources',
                                                        'popcon_dir'))
        self.config.max_popcon = int(self.read_option('data_sources', 'max_popcon'))
        self.config.clusters_dir = os.path.join(self.config.base_dir,
                                         self.read_option('data_sources',
                                                          'clusters_dir'))
        self.config.k_medoids = int(self.read_option('data_sources', 'k_medoids'))
        self.config.dde_url = self.read_option('data_sources', 'dde_url')
        self.config.dde_server = self.read_option('data_sources', 'dde_server')
        self.config.dde_port = self.read_option('data_sources', 'dde_port')

        self.config.weight = self.read_option('recommender', 'weight')
        self.config.bm25_k1 = float(self.read_option('recommender', 'bm25_k1'))
        self.config.bm25_k2 = float(self.read_option('recommender', 'bm25_k2'))
        self.config.bm25_k3 = float(self.read_option('recommender', 'bm25_k3'))
        self.config.bm25_b = float(self.read_option('recommender', 'bm25_b'))
        self.config.bm25_nl = float(self.read_option('recommender', 'bm25_nl'))
        self.config.strategy = self.read_option('recommender', 'strategy')
        self.config.profile_size = int(self.read_option('recommender',
                                                 'profile_size'))
        self.config.k_neighbors = int(self.read_option('recommender',
                                                'k_neighbors'))
        self.config.popcon_profiling = self.read_option('recommender',
                                                 'popcon_profiling')

        short_options = "hdvo:f:b:a:e:p:m:u:l:c:x:w:s:z:r:n:idvo:"
        long_options = ["help", "debug", "verbose", "output=", "filtersdir=",
                        "pkgsfilter=", "axi=", "dde=", "popconindex=",
                        "popcondir=", "indexmode=", "clustersdir=",
                        "kmedoids=", "maxpopcon=", "weight=", "strategy=",
                        "profile_size=", "profiling=", "neighbors=", "init"]
        try:
            opts, args = getopt.getopt(sys.argv[1:], short_options,
                                       long_options)
            self.options = opts
        except getopt.GetoptError as error:
            self.config.set_logger()
            logging.error("Bad syntax: %s" % str(error))
            self.usage()
            sys.exit()

        for o, p in opts:
            if o in ("-h", "--help"):
                self.usage()
                sys.exit()
            elif o in ("-d", "--debug"):
                self.config.debug = 1
            elif o in ("-v", "--verbose"):
                self.config.verbose = 1
            elif o in ("-o", "--output"):
                self.config.output = p
            elif o in ("-f", "--filtersdir"):
                self.config.filters_dir = p
            elif o in ("-b", "--pkgsfilter"):
                self.config.pkgs_filter = p
            elif o in ("-a", "--axi"):
                self.config.axi = p
            elif o in ("-e", "--dde"):
                self.config.dde_url = p
            elif o in ("-p", "--popconindex"):
                self.config.popcon_index = p
            elif o in ("-m", "--popcondir"):
                self.config.popcon_dir = p
            elif o in ("-u", "--index_mode"):
                self.config.index_mode = p
            elif o in ("-l", "--clustersdir"):
                self.config.clusters_dir = p
            elif o in ("-c", "--kmedoids"):
                self.config.k_medoids = int(p)
            elif o in ("-x", "--max_popcon"):
                self.config.max_popcon = int(p)
            elif o in ("-w", "--weight"):
                self.config.weight = p
            elif o in ("-s", "--strategy"):
                self.config.strategy = p
            elif o in ("-z", "--profile_size"):
                self.config.profile_size = int(p)
            elif o in ("-z", "--profiling"):
                self.config.profiling = p
            elif o in ("-n", "--neighbors"):
                self.config.k_neighbors = int(p)
            elif o in ("-i", "--init"):
                continue
            else:
                assert False, "unhandled option"

