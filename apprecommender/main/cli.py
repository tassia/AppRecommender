#!/usr/bin/env python

import logging
import datetime
import xapian

from apprecommender.main.app_recommender import AppRecommender
from apprecommender.recommender import Recommender
from apprecommender.user import LocalSystem
from apprecommender.config import Config
from apprecommender.initialize import Initialize
from apprecommender.load_options import LoadOptions
from apprecommender.strategy import (MachineLearning, MachineLearningBVA,
                                     MachineLearningBOW)
from apprecommender.main import collect_user_data

SUCCESS = 0
ERROR_INIT = 1
ERROR_TRAIN = 2


def check_for_flag(options, short_flag, long_flag):
    for option, _ in options:
        if option in (short_flag, long_flag):
            return True

    return False


def run_apprecommender(options):
    try:
        app_recommender = AppRecommender()
        app_recommender.make_recommendation()
        return SUCCESS
    except xapian.DatabaseOpeningError:
        return ERROR_INIT
    except IOError:
        if "ml" in Config().strategy:
            return ERROR_TRAIN


def run():
    load_options = LoadOptions()
    load_options.load()
    options = load_options.options

    if check_for_flag(options, '-i', '--init'):
        print "Initializing AppRecommender"
        initialize = Initialize()
        initialize.prepare_data()
        return SUCCESS
    elif check_for_flag(options, '-t', '--train'):
        print "Training machine learning"
        MachineLearning.train(MachineLearningBVA)
        MachineLearning.train(MachineLearningBOW)
        return SUCCESS
    elif check_for_flag(options, '-c', '--contribute'):
        collect_user_data.main()
    else:
        return run_apprecommender(load_options.options)


def main():
    result = run()

    if result is ERROR_INIT:
        print "\n"
        print "Please, Initialize AppRecommender"
        print "Run: apprec.py --init"
    elif result is ERROR_TRAIN:
        print "\n"
        print "Please, run Machine Learning Training"
        print "Run: apprec.py --train"

if __name__ == '__main__':
    main()
