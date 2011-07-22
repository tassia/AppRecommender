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

from ConfigParser import *

class Config():
    """
    Class to handle configuration options.
    """
    def __init__(self):
        """
        Set default configuration options.
        """
        self.debug = 0
        self.verbose = 0
        self.output = "/dev/null"
        self.survey_mode = 1
        self.axi = "/var/lib/apt-xapian-index/index"
        self.dde_url = "http://dde.debian.net/dde/q/udd/packages/all/%s?t=json"
        self.popcon_index = os.path.expanduser("~/.app-recommender/popcon_index")
        self.popcon_dir = os.path.expanduser("~/.app-recommender/popcon_dir")
        self.clusters_dir = os.path.expanduser("~/.app-recommender/clusters_dir")
        self.k_medoids = 100
        self.index_mode = "old"
        self.strategy = "cb"
        self.weight = "bm25"
        self.profile_size = 50
        self.load_options()
        self.set_logger()

    def usage(self):
        """
        Print usage help.
        """
        print "\n [ general ]"
        print "  -h, --help                 Print this help"
        print "  -d, --debug                Set logging level to debug"
        print "  -v, --verbose              Set logging level to verbose"
        print "  -o, --output=PATH          Path to file to save output"
        print ""
        print " [ data sources ]"
        print "  -a, --axi=PATH             Path to apt-xapian-index"
        print "  -p, --popconindex=PATH     Path to popcon index"
        print "  -m, --popcondir=PATH       Path to popcon submissions dir"
        print "  -u, --indexmode=           'old'|'reindex'|'cluster'|'recluster'"
        print "  -l, --clustersdir=PATH     Path to popcon clusters dir"
        print "  -e, --medoids=k            Number of medoids for clustering"
        print ""
        print " [ recommender ]"
        print "  -w, --weight=OPTION        Search weighting scheme"
        print "  -s, --strategy=OPTION      Recommendation strategy"
        print "  -z, --profile_size=SIZE    Size of user profile"
        print ""
        print " [ weight options ] "
        print "  trad = traditional probabilistic weighting"
        print "  bm25 = bm25 weighting scheme"
        print ""
        print " [ strategy options ] "
        print "  cb = content-based "
        print "  cbt = content-based using only tags as content "
        print "  cbd = content-based using only package descriptions as content "
        print "  col = collaborative "
        print "  colct = collaborative through tags content "

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
                              'app_recommender.cfg'])
        except (MissingSectionHeaderError), err:
            logging.error("Error in config file syntax: %s", str(err))
            os.abort()

        self.debug = self.read_option('general', 'debug')
        self.debug = self.read_option('general', 'verbose')
        self.output_filename = self.read_option('general', 'output')
        self.survey_mode = self.read_option('general', 'survey_mode')

        self.axi = self.read_option('data_sources', 'axi')
        self.dde_url = self.read_option('data_sources', 'dde_url')
        self.popcon_index = os.path.expanduser(self.read_option('data_sources','popcon_index'))
        self.popcon_dir = os.path.expanduser(self.read_option('data_sources', 'popcon_dir'))
        self.index_mode = self.read_option('data_sources', 'index_mode')
        self.clusters_dir = os.path.expanduser(self.read_option('data_sources', 'clusters_dir'))
        self.k_medoids = self.read_option('data_sources', 'k_medoids')

        self.weight = self.read_option('recommender', 'weight')
        self.strategy = self.read_option('recommender', 'strategy')
        self.profile_size = self.read_option('recommender', 'profile_size')

        short_options = "hdvo:a:p:m:ul:e:w:s:z:"
        long_options = ["help", "debug", "verbose", "output=",
                        "axi=", "popconindex=", "popcondir=", "indexmode=",
                        "clustersdir=", "kmedoids=", "weight=", "strategy=",
                        "profile_size="]
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
            elif o in ("-a", "--axi"):
                self.axi = p + "/index"
            elif o in ("-p", "--popconindex"):
                self.popcon_index = p
            elif o in ("-m", "--popcondir"):
                self.popcon_dir = p
            elif o in ("-u", "--index_mode"):
                self.index_mode = p
            elif o in ("-l", "--clustersdir"):
                self.clusters_dir = p
            elif o in ("-e", "--kmedoids"):
                self.k_medoids = p
            elif o in ("-w", "--weight"):
                self.weight = p
            elif o in ("-s", "--strategy"):
                self.strategy = p
            elif o in ("-z", "--profile_size"):
                self.strategy = p
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
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        console_handler.setLevel(log_level)
        self.logger.addHandler(console_handler)

        file_handler = logging.handlers.RotatingFileHandler(self.output,
                                                            maxBytes=5000,
                                                            backupCount=5)
        log_format = '%(asctime)s AppRecommender %(levelname)-8s %(message)s'
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)
