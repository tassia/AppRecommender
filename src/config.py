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

import sys
import os
import logging
import logging.handlers

from singleton import Singleton
from ConfigParser import ConfigParser, MissingSectionHeaderError


class Config(Singleton):
    """
    Class to handle configuration options.
    """
    def __init__(self):
        """
        Set default configuration options.
        """
        try:
            self.config_parser = ConfigParser()
            self.config_parser.read(
                ['/etc/apprecommender/recommender.conf',
                 os.path.expanduser('~/.app_recommender.rc'),
                 os.path.expanduser('app_recommender.cfg')])
        except (MissingSectionHeaderError), err:
            logging.error("Error in config file syntax: %s", str(err))
            os.abort()
        if not hasattr(self, 'initialized'):
            # data_source options
            self.base_dir = os.path.expanduser('~/.app-recommender')
            self.user_data_dir = os.path.join(self.base_dir, "user_data/")
            # general options
            self.debug = 0
            self.verbose = 1
            self.output = os.path.join(self.base_dir, "apprec.log")
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

            self.set_logger()
            self.initialized = 1
            logging.info("Basic config")

    def read_option(self, section, option):
        """
        Read option from configuration file if it is defined there or return
        default value.
        """
        var = "self.%s" % option
        if self.config_parser.has_option(section, option):
            return self.config_parser.get(section, option)
        else:
            return eval(var)

    def load_config_file(self):
        """
        Load options from configuration file and command line arguments.
        """
        config.debug = int(self.read_option('general', 'debug'))
        config.debug = int(self.read_option('general', 'verbose'))
        config.base_dir = os.path.expanduser(
            self.read_option('data_sources', 'base_dir'))
        config.user_data_dir = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'user_data_dir'))
        config.output = os.path.join(
            config.base_dir, self.read_option('general', 'output'))
        config.filters_dir = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'filters_dir'))
        config.pkgs_filter = os.path.join(
            config.filters_dir, self.read_option('data_sources',
                                                 'pkgs_filter'))
        config.axi = self.read_option('data_sources', 'axi')
        config.axi_programs = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'axi_programs'))
        config.axi_desktopapps = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'axi_desktopapps'))
        # config.index_mode = self.read_option('data_sources', 'index_mode')
        config.popcon = int(self.read_option('data_sources', 'popcon'))
        config.popcon_programs = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'popcon_programs'))
        config.popcon_desktopapps = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'popcon_desktopapps'))
        config.popcon_index = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'popcon_index'))
        config.popcon_dir = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'popcon_dir'))
        config.max_popcon = int(self.read_option('data_sources', 'max_popcon'))
        config.clusters_dir = os.path.join(
            config.base_dir, self.read_option('data_sources',
                                              'clusters_dir'))
        config.k_medoids = int(self.read_option('data_sources', 'k_medoids'))
        config.dde_url = self.read_option('data_sources', 'dde_url')
        config.dde_server = self.read_option('data_sources', 'dde_server')
        config.dde_port = self.read_option('data_sources', 'dde_port')

        config.weight = self.read_option('recommender', 'weight')
        config.bm25_k1 = float(self.read_option('recommender', 'bm25_k1'))
        config.bm25_k2 = float(self.read_option('recommender', 'bm25_k2'))
        config.bm25_k3 = float(self.read_option('recommender', 'bm25_k3'))
        config.bm25_b = float(self.read_option('recommender', 'bm25_b'))
        config.bm25_nl = float(self.read_option('recommender', 'bm25_nl'))
        config.strategy = self.read_option('recommender', 'strategy')
        config.profile_size = int(
            self.read_option('recommender', 'profile_size'))
        config.k_neighbors = int(
            self.read_option('recommender', 'k_neighbors'))
        config.popcon_profiling = self.read_option(
            'recommender', 'popcon_profiling')

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

        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        file_handler = logging.handlers.RotatingFileHandler(self.output,
                                                            maxBytes=50000000,
                                                            backupCount=5)
        log_format = '%(asctime)s %(levelname)-8s %(message)s'
        file_handler.setFormatter(logging.Formatter(
            log_format, datefmt='%Y-%m-%d %H:%M:%S'))
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)
        logging.info("Set up logger")
