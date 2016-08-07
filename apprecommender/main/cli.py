#!/usr/bin/env python

import xapian

from apprecommender.main.app_recommender import AppRecommender
from apprecommender.config import Config
from apprecommender.initialize import Initialize
from apprecommender.strategy import (MachineLearning, MachineLearningBVA,
                                     MachineLearningBOW)
from apprecommender.main import collect_user_data
from apprecommender.main.options import get_parser

SUCCESS = 0
ERROR_INIT = 1
ERROR_TRAIN = 2
PERMISSION_DENIED = 3


def parse_options(args, config):
    if args['strategy']:
        config.strategy = args['strategy']
    if args['debug']:
        config.debug = 1
    if args['verbose']:
        config.verbose = 1
    if args['profile_size']:
        config.profile_size = args['profile_size']
    if args['because']:
        config.because = True
    if args['num_recommendations']:
        config.num_recommendations = args['num_recommendations']


def get_reference_pkgs(args):
    reference_pkgs = []

    if args['package']:
        package = args['package']
        reference_pkgs.append(package)

    return reference_pkgs


def run_apprecommender(reference_pkgs):
    try:
        app_recommender = AppRecommender()
        app_recommender.make_recommendation(reference_pkgs)
        return SUCCESS
    except xapian.DatabaseOpeningError:
        return ERROR_INIT
    except IOError:
        if "ml" in Config().strategy:
            return ERROR_TRAIN
    except OSError:
        return PERMISSION_DENIED


def run(args):
    if args['init']:
        print "Initializing AppRecommender"
        initialize = Initialize()

        try:
            initialize.prepare_data()
        except OSError:
            return PERMISSION_DENIED

        return SUCCESS
    elif args['train']:
        print "Training machine learning"

        try:
            MachineLearning.train(MachineLearningBVA)
            MachineLearning.train(MachineLearningBOW)
        except IOError:
            return PERMISSION_DENIED

        return SUCCESS
    elif args['contribute']:
        collect_user_data.main()
    else:
        config = Config()
        parse_options(args, config)
        reference_pkgs = get_reference_pkgs(args)
        return run_apprecommender(reference_pkgs)


def main():
    parser = get_parser()
    args = vars(parser.parse_args())

    result = run(args)

    if result is ERROR_INIT:
        print "\n"
        print "Please, Initialize AppRecommender"
        print "Run: apprec.py --init"
    elif result is ERROR_TRAIN:
        print "\n"
        print "Please, run Machine Learning Training"
        print "Run: apprec.py --train"
    elif result is PERMISSION_DENIED:
        print "Please, run this command as sudo"

if __name__ == '__main__':
    main()
