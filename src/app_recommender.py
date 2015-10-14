#!/usr/bin/env python

import os
import logging
import datetime

from config import Config
from recommender import Recommender
from user import LocalSystem


class AppRecommender:
    def __init__(self):
        self.recommender = Recommender()

    def make_recommendation(self, recommendation_size,
                            no_auto_pkg_profile=False):
        begin_time = datetime.datetime.now()
        logging.info("Computation started at %s" % begin_time)
        # user = RandomPopcon(cfg.popcon_dir,os.path.join(cfg.filters_dir,
        #                                                 "desktopapps"))
        user = self.get_user(no_auto_pkg_profile)
        user_reccomendation = (self.recommender.get_recommendation(
                               user, recommendation_size))

        logging.info("Recommending applications for user %s" % user.user_id)
        logging.info(user_reccomendation)

        end_time = datetime.datetime.now()
        logging.info("Computation completed at %s" % end_time)
        delta = end_time - begin_time
        logging.info("Time elapsed: %d seconds." % delta.seconds)

        return user_reccomendation

    def get_user(self, no_auto_pkg_profile):
        config = Config()

        user = LocalSystem()
        user.filter_pkg_profile(
            os.path.join(config.filters_dir, "desktopapps"))
        user.maximal_pkg_profile()

        if no_auto_pkg_profile:
            user.no_auto_pkg_profile()

        return user
