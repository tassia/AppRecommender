#!/usr/bin/env python
"""
    Clustering - A python script to perform clustering of popcon data.
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
sys.path.insert(0,'../')
import logging
import datetime
from datetime import timedelta

from config import Config
from error import Error
import data
import xapian

if __name__ == '__main__':
    cfg = Config()
    begin_time = datetime.datetime.now()
    if len(sys.argv) >= 3:
        try:
            with open(sys.argv[2]) as valid:
                pkgs_list = [line.strip() for line in valid]
                logging.info("Packages list length: %d" % len(pkgs_list))
        except:
            logging.critical("File %s does not seem to be a package \
                              list" % sys.argv[2])
            raise Error
        pkgs_index = data.SampleAptXapianIndex(pkgs_list,xapian.Database(cfg.axi),
                                              sys.argv[1])
        try:
            logging.info("Sample package indexing started at %s" % begin_time)
        except:
                logging.critical("Could not create the index at %s" % sys.argv[1])
                raise Error

        end_time = datetime.datetime.now()
        print("Sample package indexing completed at %s" % end_time)
        print("Number of documents: %d" % pkgs_index.get_doccount())
        delta = end_time - begin_time
        logging.info("Time elapsed: %d seconds." % delta.seconds)
    else:
        logging.critical("Usage: pkgindex.py INDEX_PATH PKGS_LIST")
