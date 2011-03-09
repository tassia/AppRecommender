#!/usr/bin/python

#  AppRecommender - A GNU/Linux application recommender
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

from config import *
from data import *
from evaluation import *
from similarity_measure import *
from recommender import *
from strategy import *
from user import *

def set_up_recommender(cfg):
    reindex = 1 #FIXME should do it only if necessary

    if cfg.strategy == "cta":
        axi_db = xapian.Database(cfg.axi)
        app_rec = Recommender(axi_db)
        app_rec.set_strategy(AxiContentBasedStrategy())

    elif cfg.strategy == "ct":
        debtags_db = DebtagsDB(cfg.tags_db)
        if not debtags_db.load():
            logging.error("Could not load DebtagsDB from %s." % cfg.tags_db)
            sys.exit(1)
        debtags_index = DebtagsIndex(os.path.expanduser(cfg.tags_index))
        debtags_index.load(debtags_db,reindex)
        app_rec = Recommender(debtags_index)
        app_rec.set_strategy(ContentBasedStrategy())

    return app_rec

def cross_validation(recommender):
    metrics = []
    metrics.append(Precision())
    metrics.append(Recall())
    validation = CrossValidation(0.1,10,recommender,metrics)
    validation.run(user)

if __name__ == '__main__':
    cfg = Config()
    cfg.load_options()
    cfg.set_logger()
    rec = set_up_recommender(cfg)
    user = LocalSystem()
    result = rec.get_recommendation(user)
    result.print_result()
    cross_validation(rec)
