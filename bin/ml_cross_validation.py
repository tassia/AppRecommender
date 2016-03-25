#!/usr/bin/python

import sys
import logging

sys.path.insert(0, '../')

from src.ml.cross_validation import CrossValidationMachineLearning
from src.evaluation import (SimpleAccuracy, Precision, Recall, FPR,
                            F_score)


def ml_cross_validation():
    logger = logging.getLogger('')
    logger.setLevel(logging.CRITICAL)

    partition_size = 0.7
    rounds = 5
    metrics_list = [SimpleAccuracy(), Precision(), Recall(), FPR(), F_score(1)]
    labels = ['EX', 'G', 'M', 'B', 'H']
    threshold = [95, 65, 25, 10, 5]

    ml_cross_validation = CrossValidationMachineLearning(
        partition_size, rounds, metrics_list, labels, threshold)

    ml_cross_validation.run(None)
    print ml_cross_validation

if __name__ == '__main__':
    ml_cross_validation()
