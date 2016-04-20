#!/usr/bin/python

import sys
import os
import pickle
import xapian

sys.path.insert(0, "{0}/../".format(os.path.dirname(__file__)))

from src.ml.bag_of_words import BagOfWords
from src.ml.data import MachineLearningData
from src.config import Config
from src.strategy import XAPIAN_DATABASE_PATH

USER_DATA_DIR = Config().user_data_dir


def get_pkgs_list():
    with open(MachineLearningData.PKGS_CLASSIFICATIONS) as pkgs_classification:
        pkgs = pickle.load(pkgs_classification)
        return pkgs.keys()


def main():
    bag_of_words = BagOfWords()
    pkgs_list = get_pkgs_list()
    axi = xapian.Database(XAPIAN_DATABASE_PATH)

    bag_of_words.train_model(pkgs_list, axi)
    BagOfWords.save(bag_of_words, BagOfWords.BAG_OF_WORDS_MODEL)


if __name__ == '__main__':
    main()
