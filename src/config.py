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
            self.user_data_dir = os.path.join(self.base_dir, "user_data")
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
