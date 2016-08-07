#!/usr/bin/env python

import logging
import datetime

from apprecommender.recommender import Recommender
from apprecommender.user import LocalSystem
from apprecommender.config import Config


class AppRecommender:
    def __init__(self):
        self.recommender = Recommender()
        self.config = Config()

    def make_recommendation(self, reference_pkgs=None,
                            print_recommendation=True):
        begin_time = datetime.datetime.now()
        logging.info("Computation started at %s" % begin_time)

        if not reference_pkgs:
            reference_pkgs = []

        user = LocalSystem(reference_pkgs)
        recommendation_size = Config().num_recommendations
        user_recommendation = (self.recommender.get_recommendation(
                               user, recommendation_size))

        logging.info("Recommending applications for user %s" % user.user_id)
        if print_recommendation:
            print(user_recommendation)

        end_time = datetime.datetime.now()
        logging.info("Computation completed at %s" % end_time)
        delta = end_time - begin_time
        logging.info("Time elapsed: %d seconds." % delta.seconds)

        return user_recommendation
