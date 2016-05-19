#!/usr/bin/env python

import os
import sys
sys.path.insert(0, '../')
import logging
import datetime

from apprecommender.config import Config
from apprecommender.data import FilteredKnnXapianIndex
from apprecommender.ml.knn_loader import KnnLoader

if __name__ == '__main__':
    base_dir = os.path.expanduser("~/.app-recommender/")
    axi_path = os.path.join(base_dir, "axi_desktopapps")
    path = os.path.join(base_dir, "knn_desktopapps")
    tags_filter = os.path.join(base_dir, "filters/debtags")

    knn_file = os.path.join(base_dir, "knn_data")
    user_popcon_file = os.path.join(base_dir, "my_popcon")

    # set up config for logging
    cfg = Config()
    knn = KnnLoader.load(knn_file, user_popcon_file)
    submissions = knn.submissions

    begin_time = datetime.datetime.now()
    logging.info("Knn indexing started at %s" % begin_time)
    # use config file or command line options
    index = FilteredKnnXapianIndex(path, submissions, axi_path, tags_filter)

    end_time = datetime.datetime.now()
    logging.info("Knn indexing completed at %s" % end_time)
    logging.info("Number of documents (submissions): %d" %
                 index.get_doccount())

    delta = end_time - begin_time
    logging.info("Time elapsed: %d seconds." % delta.seconds)
