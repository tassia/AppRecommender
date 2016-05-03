#!/usr/bin/env python
"""
    config - python module for configuration options.
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

import getopt
import sys
import os
import logging
import logging.handlers

from ConfigParser import ConfigParser, MissingSectionHeaderError
from singleton import Singleton


class Config(Singleton):
    """
    Class to handle configuration options.
    """
    def __init__(self):
        """
        Set default configuration options.
        """
        if not hasattr(self, 'initialized'):
            # general options
            self.debug = 0
            self.verbose = 1
            self.output = "apprec.log"

            # data_source options
            self.base_dir = os.path.expanduser('~/.app-recommender')
            self.user_data_dir = 'user_data/'
            # filters for valid packages
            self.filters_dir = os.path.join(self.base_dir, "filters")
            self.pkgs_filter = os.path.join(self.filters_dir, "desktopapps")
            # package information packages
            self.axi = "/var/lib/apt-xapian-index/index"
            self.axi_programs = os.path.join(self.base_dir, "axi_programs")
            self.axi_desktopapps = os.path.join(self.base_dir,
                                                "axi_desktopapps")
            # popcon indexes
            self.index_mode = "old"
            # check if there are popcon indexes available
            self.popcon = 0
            self.popcon_programs = os.path.join(self.base_dir,
                                                "popcon_programs")
            self.popcon_desktopapps = os.path.join(self.base_dir,
                                                   "popcon_desktopapps")
            self.popcon_index = self.popcon_desktopapps
            self.popcon_dir = os.path.join(self.base_dir, "popcon-entries")
            self.max_popcon = 1000
            # popcon clustering
            self.clusters_dir = os.path.join(self.base_dir, "clusters-dir")
            self.k_medoids = 100
            # self.dde_url = "http://dde.debian.net/dde/" \
            #                "q/udd/packs/all/%s?t=json"

            self.dde_url = "http://46.4.235.200:8000/" \
                           "q/udd/packages/prio-debian-sid/%s?t=json"
            self.dde_server = "46.4.235.200"
            self.dde_port = 8000

            # recomender options
            self.strategy = "cb"
            self.weight = "bm25"
            self.bm25_k1 = 1.2
            self.bm25_k2 = 0
            self.bm25_k3 = 7
            self.bm25_b = 0.75
            self.bm25_nl = 0.5
            # user content profile size
            self.profile_size = 10
            # neighborhood size
            self.k_neighbors = 50
            # popcon profiling method: full, voted
            self.popcon_profiling = "full"

            self.load_options()
            self.set_logger()
            self.initialized = 1
            logging.info("Basic config")

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
        print "  -i, --profiling=OPTION     Profile filter strategy"
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
        var = "self.%s" % option
        if self.config.has_option(section, option):
            return self.config.get(section, option)
        else:
            return eval(var)

    def load_options(self):
        """
        Load options from configuration file and command line arguments.
        """
        try:
            self.config = ConfigParser()
            self.config.read(['/etc/apprecommender/recommender.conf',
                              os.path.expanduser('~/.app_recommender.rc'),
                              os.path.expanduser('app_recommender.cfg')])
        except (MissingSectionHeaderError), err:
            logging.error("Error in config file syntax: %s", str(err))
            os.abort()

        self.debug = int(self.read_option('general', 'debug'))
        self.debug = int(self.read_option('general', 'verbose'))
        self.base_dir = os.path.expanduser(self.read_option('data_sources',
                                           'base_dir'))
        self.user_data_dir = os.path.join(self.base_dir,
                                          self.read_option('data_sources',
                                                           'user_data_dir'))
        self.output = os.path.join(self.base_dir,
                                   self.read_option('general', 'output'))
        self.filters_dir = os.path.join(self.base_dir,
                                        self.read_option('data_sources',
                                                         'filters_dir'))
        self.pkgs_filter = os.path.join(self.filters_dir,
                                        self.read_option('data_sources',
                                                         'pkgs_filter'))
        self.axi = self.read_option('data_sources', 'axi')
        self.axi_programs = os.path.join(self.base_dir,
                                         self.read_option('data_sources',
                                                          'axi_programs'))
        self.axi_desktopapps = os.path.join(self.base_dir,
                                            self.read_option(
                                                'data_sources',
                                                'axi_desktopapps'))
        # self.index_mode = self.read_option('data_sources', 'index_mode')
        self.popcon = int(self.read_option('data_sources', 'popcon'))
        self.popcon_programs = os.path.join(self.base_dir,
                                            self.read_option(
                                                'data_sources',
                                                'popcon_programs'))
        self.popcon_desktopapps = os.path.join(self.base_dir,
                                               self.read_option(
                                                   'data_sources',
                                                   'popcon_desktopapps'))
        self.popcon_index = os.path.join(self.base_dir,
                                         self.read_option('data_sources',
                                                          'popcon_index'))
        self.popcon_dir = os.path.join(self.base_dir,
                                       self.read_option('data_sources',
                                                        'popcon_dir'))
        self.max_popcon = int(self.read_option('data_sources', 'max_popcon'))
        self.clusters_dir = os.path.join(self.base_dir,
                                         self.read_option('data_sources',
                                                          'clusters_dir'))
        self.k_medoids = int(self.read_option('data_sources', 'k_medoids'))
        self.dde_url = self.read_option('data_sources', 'dde_url')
        self.dde_server = self.read_option('data_sources', 'dde_server')
        self.dde_port = self.read_option('data_sources', 'dde_port')

        self.weight = self.read_option('recommender', 'weight')
        self.bm25_k1 = float(self.read_option('recommender', 'bm25_k1'))
        self.bm25_k2 = float(self.read_option('recommender', 'bm25_k2'))
        self.bm25_k3 = float(self.read_option('recommender', 'bm25_k3'))
        self.bm25_b = float(self.read_option('recommender', 'bm25_b'))
        self.bm25_nl = float(self.read_option('recommender', 'bm25_nl'))
        self.strategy = self.read_option('recommender', 'strategy')
        self.profile_size = int(self.read_option('recommender',
                                                 'profile_size'))
        self.k_neighbors = int(self.read_option('recommender',
                                                'k_neighbors'))
        self.popcon_profiling = self.read_option('recommender',
                                                 'popcon_profiling')

        short_options = "hdvo:f:b:a:e:p:m:u:l:c:x:w:s:z:i:n:"
        long_options = ["help", "debug", "verbose", "output=", "filtersdir=",
                        "pkgsfilter=", "axi=", "dde=", "popconindex=",
                        "popcondir=", "indexmode=", "clustersdir=",
                        "kmedoids=", "maxpopcon=", "weight=", "strategy=",
                        "profile_size=", "profiling=", "neighbors="]
        try:
            opts, args = getopt.getopt(sys.argv[1:], short_options,
                                       long_options)
        except getopt.GetoptError as error:
            self.set_logger()
            logging.error("Bad syntax: %s" % str(error))
            self.usage()
            sys.exit()

        for o, p in opts:
            if o in ("-h", "--help"):
                self.usage()
                sys.exit()
            elif o in ("-d", "--debug"):
                self.debug = 1
            elif o in ("-v", "--verbose"):
                self.verbose = 1
            elif o in ("-o", "--output"):
                self.output = p
            elif o in ("-f", "--filtersdir"):
                self.filters_dir = p
            elif o in ("-b", "--pkgsfilter"):
                self.pkgs_filter = p
            elif o in ("-a", "--axi"):
                self.axi = p
            elif o in ("-e", "--dde"):
                self.dde_url = p
            elif o in ("-p", "--popconindex"):
                self.popcon_index = p
            elif o in ("-m", "--popcondir"):
                self.popcon_dir = p
            elif o in ("-u", "--index_mode"):
                self.index_mode = p
            elif o in ("-l", "--clustersdir"):
                self.clusters_dir = p
            elif o in ("-c", "--kmedoids"):
                self.k_medoids = int(p)
            elif o in ("-x", "--max_popcon"):
                self.max_popcon = int(p)
            elif o in ("-w", "--weight"):
                self.weight = p
            elif o in ("-s", "--strategy"):
                self.strategy = p
            elif o in ("-z", "--profile_size"):
                self.profile_size = int(p)
            elif o in ("-z", "--profiling"):
                self.profiling = p
            elif o in ("-n", "--neighbors"):
                self.k_neighbors = int(p)
            else:
                assert False, "unhandled option"

    def set_logger(self):
        """
        Configure application logger and log level.
        """
        self.logger = logging.getLogger('')  # root logger is used by default
        self.logger.setLevel(logging.DEBUG)

        if self.debug == 1:
            log_level = logging.DEBUG
        elif self.verbose == 1:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'))
        console_handler.setLevel(log_level)
        self.logger.addHandler(console_handler)

        file_handler = logging.handlers.RotatingFileHandler(self.output,
                                                            maxBytes=50000000,
                                                            backupCount=5)
        log_format = '%(asctime)s %(levelname)-8s %(message)s'
        file_handler.setFormatter(logging.Formatter(
            log_format, datefmt='%Y-%m-%d %H:%M:%S'))
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)
        logging.info("Set up logger")
