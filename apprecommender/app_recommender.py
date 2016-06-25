#!/usr/bin/env python

import logging
import datetime

from apprecommender.recommender import Recommender
from apprecommender.user import LocalSystem


class AppRecommender:
    def __init__(self):
        self.recommender = Recommender()

    def make_recommendation(self, recommendation_size):
        begin_time = datetime.datetime.now()
        logging.info("Computation started at %s" % begin_time)
        # user = RandomPopcon(cfg.popcon_dir,os.path.join(cfg.filters_dir,
        #                                                 "desktopapps"))
        user = LocalSystem()
        user_reccomendation = (self.recommender.get_recommendation(
                               user, recommendation_size))

        logging.info("Recommending applications for user %s" % user.user_id)
        print (user_reccomendation)

        end_time = datetime.datetime.now()
        logging.info("Computation completed at %s" % end_time)
        delta = end_time - begin_time
        logging.info("Time elapsed: %d seconds." % delta.seconds)

        return user_reccomendation
