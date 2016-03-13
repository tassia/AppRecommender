#!/usr/bin/python

import sys
sys.path.insert(0, '../')

from src.config import Config
from src.ml.bayes_matrix import BayesMatrix

import numpy as np
import src.data_classification as data_cl

import time
import calendar
import pickle

from os import makedirs



def have_files():
    have = True
    scripts = []

    if not path.exists(USER_DATA_DIR):
        makedirs(USER_DATA_DIR)

    if not path.isfile(PKG_DATA_PATH):
        have = False
        scripts.append("pkg_time_list.py")

    if not path.isfile(DEBTAGS_PATH):
        have = False
        scripts.append("get_axipkgs.py -t XT > {0}tags.txt"
                       .format(USER_DATA_DIR))

    if not have:
        print("Run scripts to generate important files:")
        for script in scripts:
            print("-  {0}".format(script))

    return have


def main():
    if not have_files():
        exit(1)

    ml_data = MachineLearningData()
    labels = ['EX', 'G', 'M', 'B', 'H']
    threshold = [85, 75, 55, 35, 10]
    pkgs_classification = ml_data.create_data(labels, threshold)        

    all_matrix = (np.matrix(pkgs_classifications.values()))
    data_matrix = all_matrix[0:, 0:-1]
    classifications = all_matrix[0:, -1]
    order_of_classifications = ['H', 'B', 'M', 'G', 'EX']

    bayes_matrix = BayesMatrix()
    bayes_matrix.training(data_matrix, classifications,
                          order_of_classifications)

    BayesMatrix.save(bayes_matrix, MACHINE_LEARNING_TRAINING)

if __name__ == "__main__":
    main()
