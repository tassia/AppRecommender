#!/usr/bin/python

import os
import sys

sys.path.append('..')

from src.config import Config
from src.initialize import Initialize
from src.ml.pkg_time import PkgTime

USER_DATA_DIR = Config().user_data_dir


def train_machine_learning():
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)

    pkg_time = PkgTime()
    initialize = Initialize()
    folder_path = os.path.dirname(os.path.abspath(__file__))

    print("\n - Generating packages time list")
    pkg_time.create_pkg_data()

    print("\n - Generating debtags")
    debtags = initialize.get_tags()
    debtags_path = "{}/tags.txt".format(USER_DATA_DIR)
    initialize.save_list(debtags, debtags_path)

    print("\n - Making machine learning traning")
    os.system("rm -f {0}/pkgs_classifications.txt".format(USER_DATA_DIR))
    os.system("{0}/pkg_classification.py".format(folder_path))

    print("\n - Making bag of words representation")
    os.system("rm -f {0}/bow_all_terms.txt".format(USER_DATA_DIR))
    os.system("rm -f {0}/bag_of_words_model.pickle".format(USER_DATA_DIR))
    os.system("{0}/generate_bag_of_words.py".format(folder_path))

if __name__ == '__main__':
    train_machine_learning()
