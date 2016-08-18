#!/usr/bin/env python
"""
    popindex.py - generate a popcon index to be used by the recommender as the
                  users repository, based on filters provided by config
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

from apprecommender.config import Config
from apprecommender.data import FilteredPopconXapianIndex

if __name__ == '__main__':
    base_dir = os.path.expanduser("~/.app-recommender/")
    axi_path = os.path.join(base_dir, "axi_desktopapps")
    path = os.path.join(base_dir, "popcon_desktopapps")
    popcon_dir = os.path.join(base_dir, "popcon-entries")
    tags_filter = os.path.join(base_dir, "filters/debtags")

    # set up config for logging
    cfg = Config()

    begin_time = datetime.datetime.now()
    logging.info("Popcon indexing started at %s" % begin_time)
    # use config file or command line options
    index = FilteredPopconXapianIndex(path, popcon_dir, axi_path, tags_filter)

    end_time = datetime.datetime.now()
    logging.info("Popcon indexing completed at %s" % end_time)
    logging.info("Number of documents (submissions): %d" %
                 index.get_doccount())

    delta = end_time - begin_time
    logging.info("Time elapsed: %d seconds." % delta.seconds)
