#!/usr/bin/python

#  config - python module for configuration options.
#
#  Copyright (C) 2010  Tassia Camoes <tassia@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import getopt
import sys
import os
from logging import *
import logging.handlers

from ConfigParser import *

class Config():
    """
    Class to handle configuration options.
    """
    def __init__(self):
        """
        Set configuration options.
        """
        self.debug = 0
        self.verbose = 0
        self.output = "/dev/null"
        self.config = None
        self.tags_db = "/var/lib/debtags/package-tags"
        self.tags_index = "~/.app-recommender/debtags_index"
        self.axi = "/var/lib/apt-xapian-index/index"
        self.axi_values = "/var/lib/apt-xapian-index/values"
        self.strategy = "ct"    # defaults to the cheapest one
        self.reindex = 0
        self.load_options()
        self.set_logger()

    def usage(self):
        """
        Print usage help.
        """
        print "\n [ general ]"
        print "  -h, --help              Print this help"
        print "  -d, --debug             Set logging level to debug."
        print "  -v, --verbose           Set logging level to verbose."
        print "  -o, --output=PATH       Path to file to save output."
        print "  -c, --config=PATH       Path to configuration file."
        print ""
        print " [ recommender ]"
        print "  -t, --tagsdb=PATH       Path to debtags database."
        print "  -i, --tagsindex=PATH    Path to debtags dedicated index."
        print "  -r, --force-reindex     Force reindexing debtags database."
        print "  -a, --axi=PATH          Path to Apt-xapian-index."
        print "  -s, --strategy=OPTION   Recommendation strategy."
        print ""
        print " [ strategy options ] "
        print "  ct = content-based using tags "
        print "  cta = content-based using tags via apt-xapian-index"
        print "  cp = content-based using package descriptions "
        print "  col = collaborative "
        print "  colct = collaborative through tags content "
        print "  colcp = collaborative through package descriptions content "

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
                              os.path.expanduser('~/apprecommender.rc')])
        except (MissingSectionHeaderError), err:
            logging.error("Error in config file syntax: %s", str(err))
            os.abort()

        self.debug = self.read_option('general', 'debug')
        self.debug = self.read_option('general', 'verbose')
        self.output_filename = self.read_option('general', 'output')
        self.config = self.read_option('general', 'config')

        self.tags_db = self.read_option('recommender', 'tags_db')
        self.tags_index = self.read_option('recommender', 'tags_index')
        self.reindex = self.read_option('recommender', 'reindex')
        self.axi = self.read_option('recommender', 'axi')

        short_options = "hdvo:c:t:i:ra:s:"
        long_options = ["help", "debug", "verbose", "output=", "config=",
                        "tagsdb=", "tagsindex=", "reindex", "axi=", "strategy="]
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
            elif o in ("-c", "--config"):
                self.config = p
            elif o in ("-t", "--tagsdb"):
                self.tags_db = p
            elif o in ("-i", "--tagsindex"):
                self.tags_index = p
            elif o in ("-r", "--force-reindex"):
                self.reindex = 1
            elif o in ("-a", "--axi"):
                self.axi = p + "/index"
                self.axi_values = p + "/values"
            elif o in ("-s", "--strategy"):
                self.strategy = p
            else:
                assert False, "unhandled option"

    def set_logger(self):
        """
        Configure application logger and log level.
        """
        self.logger = getLogger('')  # root logger is used by default
        self.logger.setLevel(DEBUG)

        if self.debug == 1:
            log_level = DEBUG
        elif self.verbose == 1:
            log_level = INFO
        else:
            log_level = WARNING

        console_handler = StreamHandler(sys.stdout)
        console_handler.setFormatter(Formatter('%(levelname)s: %(message)s'))
        console_handler.setLevel(log_level)
        self.logger.addHandler(console_handler)

        file_handler = logging.handlers.RotatingFileHandler(self.output,
                                                            maxBytes=5000,
                                                            backupCount=5)
        log_format = '%(asctime)s AppRecommender %(levelname)-8s %(message)s'
        file_handler.setFormatter(Formatter(log_format))
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)
