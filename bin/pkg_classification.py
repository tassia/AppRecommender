#!/usr/bin/python

import os
import sys

sys.path.insert(0, "{0}/../".format(os.path.dirname(__file__)))

from src.ml.data import MachineLearningData
from src.ml.bayes_matrix import BayesMatrix

import numpy as np

from os import makedirs
from os import path


def have_files():
    have = True
    scripts = []

    if not path.exists(MachineLearningData.USER_DATA_DIR):
        makedirs(MachineLearningData.USER_DATA_DIR)

    if not path.isfile(MachineLearningData.PKG_DATA_PATH):
        have = False
        scripts.append("pkg_time_list.py")

    if not have:
        print("Run scripts to generate important files:")
        for script in scripts:
            print("-  {0}".format(script))

    return have


def main():
    if not have_files():
        exit(1)

    ml_data = MachineLearningData()
    labels = ['RU', 'U', 'NU']
    pkgs_classifications = ml_data.create_data(labels)

    all_matrix = (np.matrix(pkgs_classifications.values()))
    data_matrix = all_matrix[0:, 0:-1]
    classifications = all_matrix[0:, -1]
    order_of_classifications = ['NU', 'U', 'RU']

    bayes_matrix = BayesMatrix()
    bayes_matrix.training(data_matrix, classifications,
                          order_of_classifications)

    BayesMatrix.save(bayes_matrix,
                     MachineLearningData.MACHINE_LEARNING_TRAINING)

if __name__ == "__main__":
    main()
