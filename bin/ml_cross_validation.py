#!/usr/bin/python

import argparse
import datetime as dt
import logging
import os
import pickle
import sys

sys.path.insert(0, "{0}/../".format(os.path.dirname(__file__)))

from src.ml.cross_validation import (CrossValidationBVA, CrossValidationBOW)
from src.evaluation import (SimpleAccuracy, Precision, Recall, FPR,
                            F_score)
from src.ml.data import MachineLearningData
from src.ml.bag_of_words import BagOfWords
from src.config import Config


BASE_DIR = Config().base_dir
CROSS_VALIDATION_FOLDER = BASE_DIR + '/cross_validation_data/'


def get_strategy(ml_strategy_str, pkg_data, partition_size, rounds,
                 metrics_list, labels, threshold):
    if ml_strategy_str == 'bow':
        return CrossValidationBOW(
            pkg_data, partition_size, rounds, metrics_list,
            labels, threshold)
    else:
        return CrossValidationBVA(
            pkg_data, partition_size, rounds, metrics_list,
            labels, threshold)


def get_pkg_data(ml_strategy_str, ml_data, labels, threshold):
    if ml_strategy_str == 'bow':
        path = BagOfWords.BAG_OF_WORDS_PKGS_CLASSIFICATION
        with open(path, 'ra') as pkgs_classification:
            return pickle.load(pkgs_classification)
    else:
        return ml_data.create_data(labels, threshold)


def ml_cross_validation(folder_path, ml_strategy_str):
    logger = logging.getLogger('')
    logger.setLevel(logging.CRITICAL)

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    partition_size = 0.8
    rounds = 5
    metrics_list = [SimpleAccuracy(), Precision(), Recall(), FPR(), F_score(1)]
    labels = ['EX', 'G', 'M', 'B', 'H']
    threshold = [95, 65, 25, 10, 5]

    ml_data = MachineLearningData()
    pkg_data = get_pkg_data(ml_strategy_str, ml_data, labels, threshold)
    ml_cross_validation = get_strategy(
        ml_strategy_str, pkg_data, partition_size, rounds,
        metrics_list, labels, threshold)

    cross_validaton_file = 'cross_validation_result_{0}_{1}_{2}.txt'.format(
        rounds, partition_size, dt.datetime.now().strftime('%Y%m%d%H%M'))

    ml_cross_validation.run(None)

    cross_validation_file_path = folder_path + cross_validaton_file
    with open(cross_validation_file_path, 'w') as result:
        result.write(ml_cross_validation.__str__())

    return ml_cross_validation


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "s", type=str,
        help="the cross validation strategy\nbvo: bag of words\nbva: binary\
              vector")

    args = parser.parse_args()
    ml_strategy_str = args.s
    print ml_cross_validation(CROSS_VALIDATION_FOLDER, ml_strategy_str)
    print ("Cross validation results saved on: %s" %
           (CROSS_VALIDATION_FOLDER))
