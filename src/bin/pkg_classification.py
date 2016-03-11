#!/usr/bin/python

import sys
sys.path.insert(0, '../')

from data_classification import linear_percent_function
from config import Config
from os import path

import numpy as np
import data_classification as data_cl

import bayes_matrix
import time
import calendar
import xapian
import pickle

from os import path, makedirs

USER_DATA_DIR = Config().user_data_dir
BASE_DIR = Config().base_dir
XAPIAN_DATABASE_PATH = path.expanduser('~/.app-recommender/axi_desktopapps/')


def sample_classification(percent):
    if percent >= 80:
        return 'EX'
    elif percent >= 70:
        return 'G'
    elif percent >= 50:
        return 'M'
    elif percent >= 30:
        return 'B'
    else:
        return 'H'


def get_pkgs_classification(percent_function, classification_function):
    pkgs = {}
    time_now = calendar.timegm(time.gmtime())

    with open(USER_DATA_DIR + 'pkg_data.txt', 'r') as pkg_data:
        for pkg_line in pkg_data:
            name, modify, access = pkg_line.split(' ')

            percent = percent_function(modify, access, time_now)

            pkgs[name] = classification_function(percent * 100)

    return pkgs


def get_pkg_data(axi, pkg_name, data_type):
    pkg_name = 'XP' + pkg_name

    query = xapian.Query(xapian.Query.OP_OR, [pkg_name])
    enquire = xapian.Enquire(axi)
    enquire.set_query(query)

    mset = enquire.get_mset(0, 10)

    pkg_info = []
    for pkg in mset:
        for term in axi.get_document(pkg.docid).termlist():

            pkg_term = term.term

            if pkg_term.startswith(data_type):
                pkg_info.append(pkg_term[len(data_type):])
            elif data_type == 'term':
                if pkg_term.startswith('Z') or pkg_term[0].islower():
                    pkg_info.append(pkg_term)

    return pkg_info


def get_pkg_debtags(axi, pkg_name):
    return get_pkg_data(axi, pkg_name, 'XT')


def get_pkg_terms(axi, pkg_name):
    return get_pkg_data(axi, pkg_name, 'term')


def get_debtags_name(file_path):
    with open(file_path, 'r') as text:
        debtags_name = [debtag.strip() for debtag in text]

    return debtags_name


def create_row_table_list(labels_name, pkg_elements):
    row_list = []

    for debtag in labels_name:
        row_list.append(1 if debtag in pkg_elements else 0)

    return row_list


def get_terms_for_all_pkgs(axi, pkgs):
    pkg_terms = set()
    for pkg in pkgs:
        pkg_terms = pkg_terms | set(get_pkg_terms(axi, pkg))

    return pkg_terms


def filter_terms(pkg_terms):

    data_cl.generate_all_terms_tfidf()
    tfidf_weights = data_cl.user_tfidf_weights
    tfidf_threshold = sum(tfidf_weights.values())/len(tfidf_weights)

    for term in pkg_terms.copy():
        tfidf = data_cl.term_tfidf_weight_on_user(term)

        if tfidf <= tfidf_threshold:
            pkg_terms.remove(term)


def get_pkgs_table_classification(axi, pkgs, debtags_name, terms_name):
    pkgs_classification = {}

    for key, value in pkgs.iteritems():

        pkgs_classification[key] = []

        debtags = get_pkg_debtags(axi, key)
        debtags = create_row_table_list(debtags_name, debtags)
        pkgs_classification[key].extend(debtags)

        terms = get_pkg_terms(axi, key)
        terms = create_row_table_list(list(terms_name), terms)
        pkgs_classification[key].extend(terms)

        pkgs_classification[key].append(value)

    return pkgs_classification


def have_files():
    have = True
    scripts = []

    if not path.exists(USER_DATA_DIR):
        makedirs(USER_DATA_DIR)

    if not path.isfile(USER_DATA_DIR + 'pkg_data.txt'):
        have = False
        scripts.append("pkg_time_list.py")

    if not path.isfile(USER_DATA_DIR + 'tags.txt'):
        have = False
        scripts.append("get_axipkgs.py -t XT > {0}tags.txt".format(USER_DATA_DIR))

    if not have:
        print("Run scripts to generate important files:")
        for script in scripts:
            print("-  {0}".format(script))

    return have


def main():
    if not have_files():
        exit(1)

    axi = xapian.Database(XAPIAN_DATABASE_PATH)
    pkgs = get_pkgs_classification(data_cl.linear_percent_function,
                                   sample_classification)

    debtags_name = get_debtags_name(BASE_DIR + '/filters/debtags')
    terms_name = get_terms_for_all_pkgs(axi, pkgs.keys())
    filter_terms(terms_name)
    terms_name = sorted(terms_name)

    pkgs_classifications = (get_pkgs_table_classification(axi, pkgs,
                            debtags_name, terms_name))
    pkgs_classifications_indices = debtags_name + terms_name

    with open(USER_DATA_DIR + 'pkgs_classifications_indices.txt', 'wb') as text:
        pickle.dump(pkgs_classifications_indices, text)

    with open(USER_DATA_DIR + 'pkg_classification.txt', 'wb') as text:
        pickle.dump(pkgs_classifications, text)

    all_matrix = (np.matrix(pkgs_classifications.values()))
    attribute_matrix = all_matrix[0:, 0:-1]
    classifications = all_matrix[0:, -1]
    order_of_classifications = ['H', 'B', 'M', 'G', 'EX']

    bayes_matrix.training(attribute_matrix, classifications, order_of_classifications)

if __name__ == "__main__":
    main()
