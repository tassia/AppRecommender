#!/usr/bin/env python
"""
    pkgindex.py - generate a pkgs index to be used by the recommender as the
                  items repository, based on the pkgs filter provided by config
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

import os
import sys
sys.path.insert(0, '../')
import logging
import datetime

from config import Config
import data
import xapian

if __name__ == '__main__':
    cfg = Config()
    begin_time = datetime.datetime.now()
    logging.info("Sample package indexing started at %s" % begin_time)
    with open(cfg.pkgs_filter) as valid:
        pkgs_list = [line.strip() for line in valid]
        logging.info("Packages list length: %d" % len(pkgs_list))

    # use config file or command line options
    pkgs_filter = cfg.pkgs_filter.lstrip(cfg.filters_dir)
    pkgindex = data.SampleAptXapianIndex(pkgs_list, xapian.Database(cfg.axi),
                                         os.path.join(cfg.base_dir,
                                         "axi_"+pkgs_filter))
    end_time = datetime.datetime.now()
    logging.info("Sample package indexing completed at %s" % end_time)
    logging.info("Number of documents (packages): %d" %
                 pkgindex.get_doccount())

    delta = end_time - begin_time
    logging.info("Time elapsed: %d seconds." % delta.seconds)
