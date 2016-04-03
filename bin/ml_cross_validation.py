#!/usr/bin/python

import sys
import os
import logging
import datetime as dt

sys.path.insert(0, "{0}/../".format(os.path.dirname(__file__)))

from src.config import Config
from src.ml.cross_validation import CrossValidationMachineLearning
from src.evaluation import (SimpleAccuracy, Precision, Recall, FPR,
                            F_score)
from src.ml.data import MachineLearningData


BASE_DIR = Config().base_dir
CROSS_VALIDATION_FOLDER = BASE_DIR + '/cross_validation_data/'


def ml_cross_validation(folder_path):
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
    pkg_data = ml_data.create_data(labels, threshold)

    cross_validaton_file = 'cross_validation_result_{0}_{1}_{2}.txt'.format(
        rounds, partition_size, dt.datetime.now().strftime('%Y%m%d%H%M'))

    ml_cross_validation = CrossValidationMachineLearning(
        pkg_data, partition_size, rounds, metrics_list,
        labels, threshold)

    ml_cross_validation.run(None)

    cross_validation_file_path = folder_path + cross_validaton_file
    with open(cross_validation_file_path, 'w') as result:
        result.write(ml_cross_validation.__str__())

    print ml_cross_validation


if __name__ == '__main__':
    ml_cross_validation(CROSS_VALIDATION_FOLDER)
    print ("Cross validation results saved on: %s" %
           (CROSS_VALIDATION_FOLDER))
