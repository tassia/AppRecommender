#!/usr/bin/python

import sys
sys.path.insert(0, '../')

from data_classification import linear_percent_function

import time
import calendar
import xapian
import pickle

XAPIAN_DATABASE_PATH = '/var/lib/apt-xapian-index/index'


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

    with open('pkg_data.txt', 'r') as pkg_data:
        for pkg_line in pkg_data:
            name, modify, access = pkg_line.split(' ')

            percent = percent_function(modify, access, time_now)

            pkgs[name] = classification_function(percent * 100)

    return pkgs


def get_pkg_data(axi, pkg_name, data_type):
    pkg_name = 'XP'+pkg_name

    query = xapian.Query(xapian.Query.OP_OR, [pkg_name])
    enquire = xapian.Enquire(axi)
    enquire.set_query(query)

    mset = enquire.get_mset(0, 10)

    pkg_info = []
    for pkg in mset:
        for term in axi.get_document(pkg.docid).termlist():
            if term.term.startswith(data_type):
                pkg_info.append(term.term[len(data_type):])

    return pkg_info


def get_pkg_debtags(axi, pkg_name):
    return get_pkg_data(axi, pkg_name, 'XT')


def get_pkg_terms(axi, pkg_name):
    return get_pkg_data(axi, pkg_name, 'Z')


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


def main():
    axi = xapian.Database(XAPIAN_DATABASE_PATH)
    pkgs = get_pkgs_classification(linear_percent_function,
                                   sample_classification)

    debtags_name = get_debtags_name('tags.txt')
    terms_name = sorted(get_terms_for_all_pkgs(axi, pkgs.keys()))

    pkgs_classifications = (get_pkgs_table_classification(axi, pkgs,
                            debtags_name, terms_name))

    with open('pkg_classification.txt', 'wb') as text:
        pickle.dump(pkgs_classifications, text)


if __name__ == "__main__":
    main()
