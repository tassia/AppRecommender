#!/usr/bin/python

#  CrossValidation - python module for classes and methods related to
#                    recommenders evaluation.
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

import os
import sys
import logging
import datetime
from datetime import timedelta

from config import *
from data import *
from evaluation import *
from similarity import *
from recommender import *
from strategy import *
from user import *
from error import Error

if __name__ == '__main__':
    try:
        cfg = Config()
        rec = Recommender(cfg)
        user = LocalSystem()
        user.maximal_pkg_profile()

        begin_time = datetime.datetime.now()
        logging.debug("Cross-validation started at %s" % begin_time)

        metrics = []
        metrics.append(Precision())
        metrics.append(Recall())
        validation = CrossValidation(0.3,10,rec,metrics)
        validation.run(user)
        print validation

        end_time = datetime.datetime.now()
        logging.debug("Cross-validation completed at %s" % end_time)
        delta = end_time - begin_time
        logging.info("Time elapsed: %d seconds." % delta.seconds)

    except Error:
        logging.critical("Aborting proccess. Use '--debug' for more details.")
