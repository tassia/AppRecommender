#!/usr/bin/env python

import xapian

from apprecommender.collaborative_data import CollaborativeDataError
from apprecommender.config import Config
from apprecommender.initialize import Initialize
from apprecommender.strategy import (MachineLearning, MachineLearningBVA,
                                     MachineLearningBOW,
                                     MachineLearningTrainError)
from apprecommender.main.app_recommender import AppRecommender
from apprecommender.main import collect_user_data
from apprecommender.main import show_classifications
from apprecommender.main.apt_run import AptRun
from apprecommender.main.options import get_parser

SUCCESS = 0
ERROR_INIT = 1
ERROR_TRAIN = 2
PERMISSION_DENIED = 3
ERROR_INIT_TRAIN = 4


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
    if args['with_collaborative']:
        config.use_collaborative_desktopapps()


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


def run_initialize():
    print "Initializing AppRecommender"
    initialize = Initialize()

    try:
        initialize.prepare_data()
    except OSError:
        return PERMISSION_DENIED

    return SUCCESS


def run_train():
    print "Training machine learning"

    try:
        MachineLearning.train(MachineLearningBVA)
        MachineLearning.train(MachineLearningBOW)
    except IOError:
        return PERMISSION_DENIED
    except MachineLearningTrainError:
        return ERROR_INIT_TRAIN

    return SUCCESS


def run_update_collaborative_data():
    print "Updating collaborative data"
    initialize = Initialize()

    try:
        initialize.update_collaborative_data()
    except OSError:
        return PERMISSION_DENIED
    except CollaborativeDataError as error:
        print error

    return SUCCESS


def run(args):
    if args['update']:
        init_result = run_initialize()

        if init_result != SUCCESS:
            return init_result

        train_result = run_train()

        if train_result != SUCCESS:
            return train_result

        return SUCCESS
    elif args['init']:
        return run_initialize()
    elif args['train']:
        return run_train()
    elif args['update_collaborative_data']:
        return run_update_collaborative_data()
    elif args['contribute']:
        collect_user_data.main()
    elif args['show_classifications']:
        show_classifications.main()
    elif args['enable_apt']:
        try:
            apt_run = AptRun()
            if apt_run.enable():
                print 'AppRecommender now makes recommendations when you ' \
                      ' install new packages with apt'
            else:
                print 'This is already enabled'

            return SUCCESS
        except OSError:
            return PERMISSION_DENIED
    elif args['disable_apt']:
        try:
            apt_run = AptRun()
            if apt_run.disable():
                print 'AppRecommender now dont makes recommendations when' \
                      'you install new packages with apt'
            else:
                print 'This is already disabled'

            return SUCCESS
        except OSError:
            return PERMISSION_DENIED
    else:
        config = Config()
        parse_options(args, config)
        reference_pkgs = args['packages']
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
    elif result is ERROR_INIT_TRAIN:
        print 'Error: You need install more packages to use machine' \
              ' learning recommendations'

if __name__ == '__main__':
    main()
