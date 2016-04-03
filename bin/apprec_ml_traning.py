#!/usr/bin/python

import os
import sys

sys.path.append('..')

from src.config import Config

USER_DATA_DIR = Config().user_data_dir


def train_machine_learning(folder_path):
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)

    print("\n - Generating packages time list")
    os.system("{0}pkg_time_list.py".format(folder_path))

    print("\n - Generating debtags")
    os.system("{0}get_axipkgs.py -t XT > {1}tags.txt".format(folder_path,
                                                             USER_DATA_DIR))

    print("\n - Making machine learning traning")
    os.system("rm -f {0}pkgs_classifications.txt".format(USER_DATA_DIR))
    os.system("{0}pkg_classification.py".format(folder_path))

    print("\n - Making bag of words representation")
    os.system("rm -f {0}bow_all_terms.txt".format(USER_DATA_DIR))
    os.system("rm -f {0}bag_of_words_model.pickle".format(USER_DATA_DIR))
    os.system("{0}generate_bag_of_words.py".format(folder_path))

if __name__ == '__main__':
    train_machine_learning('./')
