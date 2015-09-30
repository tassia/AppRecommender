#!/usr/bin/env python
"""
    indexer.py - generate xapian indexes to be used as items and users
                 repositories
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
import datetime

from config import Config
import data
import xapian

if __name__ == '__main__':
    axi_path = "/var/lib/apt-xapian-index/index"
    cfg = Config()
    axi = xapian.Database(axi_path)
    base_dir = cfg.base_dir

    begin_time = datetime.datetime.now()

    # axi sample based on the pkgs sample provided by command line
    if "sample" in sys.argv:
        print ("Sample package indexing started at %s" % begin_time)
        if len(sys.argv) > 2:
            pkgs_filter = sys.argv[2]
        else:
            print "Usage: indexer axi_sample pkgs_sample_file"
            exit(1)
        with open(pkgs_filter) as valid:
            pkgs_list = [line.strip() for line in valid]
        filter_str = pkgs_filter.split("/")[-1]

        index = data.SampleAptXapianIndex(pkgs_list, axi,
                                          os.path.join(base_dir,
                                                       "axi_"+filter_str))
        print ("Axi size: %d" % axi.get_doccount())
        print ("Packages list length: %d" % len(pkgs_list))
        print ("Sample index size: %d" % index.get_doccount())

    # axi filtered by terms provided by command line
    if "filter" in sys.argv:
        print ("Filtered package indexing started at %s" % begin_time)
        if len(sys.argv) > 2:
            terms = sys.argv[2:]
        else:
            print ("Usage: indexer axi_filter term [additional terms]")
            exit(1)
        terms_str = "_".join([t.split("::")[-1] for t in terms])
        index = data.FilteredXapianIndex(terms, axi,
                                         os.path.join(base_dir,
                                                      "axi_"+terms_str))
        print ("Axi size: %d" % axi.get_doccount())
        print ("Terms filter: %s" % terms)
        print ("Filtered index size: %d" % index.get_doccount())

    end_time = datetime.datetime.now()
    print ("Indexing completed at %s" % end_time)
    delta = end_time - begin_time
    print ("Time elapsed: %d seconds." % delta.seconds)
