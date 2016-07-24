#!/usr/bin/python

import datetime as dt
import logging
import os
import pickle
import sys
import getopt

from apprecommender.ml.cross_validation import (CrossValidationBVA,
                                                CrossValidationBOW)
from apprecommender.evaluation import (SimpleAccuracy, Precision, Recall, FPR,
                                       F_score)
from apprecommender.ml.data import MachineLearningData
from apprecommender.ml.bag_of_words import BagOfWords
from apprecommender.config import Config


BASE_DIR = Config().base_dir
CROSS_VALIDATION_FOLDER = BASE_DIR + '/cross_validation_data/'


def get_strategy(ml_strategy_str, pkg_data, partition_size, rounds,
                 metrics_list, labels):
    if ml_strategy_str == 'bow':
        return CrossValidationBOW(
            pkg_data, partition_size, rounds, metrics_list,
            labels)
    else:
        return CrossValidationBVA(
            pkg_data, partition_size, rounds, metrics_list,
            labels)


def get_pkg_data(ml_strategy_str, ml_data, labels):
    if ml_strategy_str == 'bow':
        path = BagOfWords.BAG_OF_WORDS_PKGS_CLASSIFICATION
        with open(path, 'ra') as pkgs_classification:
            return pickle.load(pkgs_classification)
    else:
        return ml_data.create_data(labels)


def ml_cross_validation(folder_path, ml_strategy_str):
    logger = logging.getLogger('')
    logger.setLevel(logging.CRITICAL)

    if folder_path[-1] != '/':
        folder_path += '/'

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    partition_size = 0.8
    rounds = 5
    metrics_list = [SimpleAccuracy(), Precision(), Recall(), FPR(), F_score(1)]
    labels = ['RU', 'U', 'NU']

    ml_data = MachineLearningData()
    pkg_data = get_pkg_data(ml_strategy_str, ml_data, labels)
    ml_cross_validation = get_strategy(
        ml_strategy_str, pkg_data, partition_size, rounds,
        metrics_list, labels)

    cross_validaton_file = 'cross_validation_result_{}_{}_{}_{}.txt'.format(
        ml_strategy_str, rounds, partition_size,
        dt.datetime.now().strftime('%Y%m%d%H%M'))

    ml_cross_validation.run(None)

    cross_validation_file_path = folder_path + cross_validaton_file
    with open(cross_validation_file_path, 'w') as result:
        result.write(ml_cross_validation.__str__())

    return ml_cross_validation


def print_help():
    print "\n"
    print "Usage: get_axipkgs"
    print " -h, --help \t\t Show this help"
    print " -s, --strategy \t Set machine_learning of one strategy" \
          ", exemple: bva, bow"
    print "\n"
    print " [ strategy options ] "
    print " bva - run cross_validation from mlbva, Binary Vector" \
          " Approach"
    print " bow - run cross_validation from mlbow, Bag of Words"


if __name__ == '__main__':
    short_options = "hdvo:s:"
    long_options = ["help", "strategy"]
    valid_strategies = ['bva', 'bow']
    ml_strategy_str = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], short_options,
                                   long_options)
    except getopt.GetoptError as error:
        logging.error("Bad syntax: %s" % str(error))
        print_help()
        sys.exit()

    for option, param in opts:
        if option in ("-h", "--help"):
            print_help()
            sys.exit()
        elif option in ("-s", "--strategy"):
            ml_strategy_str = param
        else:
            print_help()
            assert False, "unhandled option"

    if ml_strategy_str in valid_strategies:
        print ml_cross_validation(CROSS_VALIDATION_FOLDER, ml_strategy_str)
        print("Cross validation results saved on: %s" %
              (CROSS_VALIDATION_FOLDER))
    else:
        print_help()
