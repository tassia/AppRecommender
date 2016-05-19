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

import os
import logging
import datetime
import sys

sys.path.insert(0, '../')

from apprecommender.config import Config
from apprecommender.evaluation import (CrossValidation, Precision, Recall,
                                       F_score, FPR, Accuracy)
from apprecommender.recommender import Recommender
from apprecommender.user import PopconSystem

if __name__ == '__main__':
    cfg = Config()
    rec = Recommender()
    # user = LocalSystem()
    # user = RandomPopcon(cfg.popcon_dir)
    # user = RandomPopcon(cfg.popcon_dir,os.path.join(cfg.filters_dir,
    #                                                 "desktopapps"))

    popcon_entries = "~/.app-recommender/popcon-entries/" \
                     "00/0001166d0737c6dffb083071e5ee69f5"
    user = PopconSystem(os.path.expanduser(popcon_entries))
    user.filter_pkg_profile(os.path.join(cfg.filters_dir, "desktopapps"))
    user.maximal_pkg_profile()
    begin_time = datetime.datetime.now()

    metrics = []
    metrics.append(Precision())
    metrics.append(Recall())
    metrics.append(F_score(0.5))
    metrics.append(Accuracy())
    metrics.append(FPR())
    validation = CrossValidation(0.9, 20, rec, metrics, 0.005)
    validation.run(user)
    print validation

    end_time = datetime.datetime.now()
    delta = end_time - begin_time
    logging.info("Cross-validation for user %s" % user.user_id)
    logging.info("Recommender strategy: %s" % rec.strategy.description)
    logging.debug("Cross-validation started at %s" % begin_time)
    logging.debug("Cross-validation completed at %s" % end_time)
    logging.info("Time elapsed: %d seconds." % delta.seconds)
