#!/usr/bin/python

import sys
import os
import logging
import datetime as dt

sys.path.insert(0, '../')

from src.config import Config
from src.ml.cross_validation import CrossValidationMachineLearning
from src.evaluation import (SimpleAccuracy, Precision, Recall, FPR,
                            F_score)


BASE_DIR = Config().base_dir
CROSS_VALIDATION_FOLDER = BASE_DIR + '/cross_validation_data/'


def ml_cross_validation():
    logger = logging.getLogger('')
    logger.setLevel(logging.CRITICAL)

    if not os.path.exists(CROSS_VALIDATION_FOLDER):
        os.mkdir(CROSS_VALIDATION_FOLDER)

    partition_size = 0.7
    rounds = 5
    metrics_list = [SimpleAccuracy(), Precision(), Recall(), FPR(), F_score(1)]
    labels = ['EX', 'G', 'M', 'B', 'H']
    threshold = [95, 65, 25, 10, 5]

    cross_validaton_file = 'cross_validation_result_{0}_{1}_{2}'.format(
        rounds, partition_size, dt.datetime.now().strftime('%Y%m%d%H%M'))

    ml_cross_validation = CrossValidationMachineLearning(
        partition_size, rounds, metrics_list, labels, threshold)

    ml_cross_validation.run(None)

    cross_validation_file_path = CROSS_VALIDATION_FOLDER + cross_validaton_file
    with open(cross_validation_file_path, 'w') as result:
        result.write(ml_cross_validation.__str__())

    print ("Cross validation results saved on: %s" %
           (cross_validation_file_path))

if __name__ == '__main__':
    ml_cross_validation()
