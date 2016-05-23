#!/usr/bin/env python
"""
    CrossValidation - python module for classes and methods related to
                      recommenders evaluation.
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
sys.path.insert(0, '../')
import logging
import datetime

from apprecommender.config import Config
from apprecommender.evaluation import (Precision, Recall, F1, Accuracy,
                                       SimpleAccuracy, CrossValidation)
from apprecommender.recommender import Recommender
from apprecommender.user import LocalSystem
from apprecommender.error import Error

if __name__ == '__main__':
    try:
        cfg = Config()
        rec = Recommender(cfg)
        print "\nRecommender strategy: ", rec.strategy.description
        user = LocalSystem()
        begin_time = datetime.datetime.now()
        logging.debug("Cross-validation started at %s" % begin_time)

        metrics = []
        metrics.append(Precision())
        metrics.append(Recall())
        metrics.append(F1())
        metrics.append(Accuracy())
        metrics.append(SimpleAccuracy())
        validation = CrossValidation(0.9, 10, rec, metrics, 0.1)
        validation.run(user)
        print validation

        end_time = datetime.datetime.now()
        logging.debug("Cross-validation completed at %s" % end_time)
        delta = end_time - begin_time
        logging.info("Time elapsed: %d seconds." % delta.seconds)

    except Error:
        logging.critical("Aborting proccess. Use '--debug' for more details.")
