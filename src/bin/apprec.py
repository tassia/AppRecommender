#!/usr/bin/env python
"""
    AppRecommender - A GNU/Linux application recommender
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
sys.path.insert(0,'../')
import logging
import datetime
import random
from datetime import timedelta

from config import *
from data import *
from evaluation import *
from dissimilarity import *
from recommender import *
from strategy import *
from user import *
from error import Error

if __name__ == '__main__':
    try:
        begin_time = datetime.datetime.now()
        logging.debug("Computation started at %s" % begin_time)
        cfg = Config()
        rec = Recommender(cfg)
        user = RandomPopcon(cfg.popcon_dir,os.path.join(cfg.filters,"desktop"))
        #user = LocalSystem()
        user.filter_pkg_profile(os.path.join(cfg.filters,"desktop"))
        user.maximal_pkg_profile()

        logging.info("Recommending applications for user %s" % user.user_id)
        logging.info(rec.get_recommendation(user,20))

        end_time = datetime.datetime.now()
        logging.debug("Computation completed at %s" % end_time)
        delta = end_time - begin_time
        logging.info("Time elapsed: %d seconds." % delta.seconds)

    except Error:
        logging.critical("Aborting proccess. Use '--debug' for more details.")

