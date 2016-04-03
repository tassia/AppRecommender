#!/usr/bin/python

import sys
import os

sys.path.insert(0, "{0}/../".format(os.path.dirname(__file__)))

from src.ml.data import MachineLearningData
from src.ml.bag_of_words import BagOfWords
from src.config import Config

USER_DATA_DIR = Config().user_data_dir

import apt
import nltk
import re
import pickle

nltk.download('stopwords')

from nltk.corpus import stopwords


def get_train_and_label(pkgs_description, pkg_data):
    descriptions = []
    labels = []

    for pkg, description in pkgs_description.iteritems():
        descriptions.append(description)
        labels.append(pkg_data[pkg][-1])

    return (descriptions, labels)


def main():
    cache = apt.Cache()

    pkgs_description = {}
    stop_words = set(stopwords.words('english'))

    ml_data = MachineLearningData()
    pkg_data = ml_data.create_data(None, None)

    for pkg in pkg_data.keys():
        description = cache[pkg].versions[0].description.strip()

        # Remove any other character that is not a letter
        description = re.sub('[^a-zA-Z]', ' ', description)
        description = description.lower()
        description = description.split()

        description = [word for word in description if word not in stop_words]

        pkgs_description[pkg] = ' '.join(description)

    descriptions, labels = get_train_and_label(pkgs_description, pkg_data)

    bag_of_words = BagOfWords()
    all_terms = bag_of_words.generate_valid_terms(descriptions)

    pkgs = zip(descriptions, labels)
    bag_of_words.train_model(pkgs)

    with open(USER_DATA_DIR + '/bow_all_terms.pickle', 'wa') as bow_terms:
        pickle.dump(all_terms, bow_terms)


if __name__ == '__main__':
    main()
