#!/usr/bin/python

import time
import calendar
import xapian
import pickle

XAPIAN_DATABASE_PATH = '/var/lib/apt-xapian-index/index'


def linear_percent_function(modify, access, time_now):
    modify, access = int(modify), int(access)

    time_access = access - modify
    time_actual = time_now - modify

    percent = float(time_access) * 100.0 / float(time_actual)

    return percent


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

            pkgs[name] = classification_function(percent)

    return pkgs


def get_pkg_debtags(axi, pkg_name):
    pkg_name = 'XP'+pkg_name

    query = xapian.Query(xapian.Query.OP_OR, [pkg_name])
    enquire = xapian.Enquire(axi)
    enquire.set_query(query)

    mset = enquire.get_mset(0, 10)

    pkg_info = []
    for pkg in mset:
        for term in axi.get_document(pkg.docid).termlist():
            if term.term.startswith('XT'):
                pkg_info.append(term.term[2:])

    return pkg_info


def get_debtags_name(file_path):
    with open(file_path, 'r') as text:
        debtags_name = [debtag.strip() for debtag in text]

    return debtags_name


def create_debtag_list(debtags_name, pkg_debtag):
    debtag_list = []

    for debtag in debtags_name:
        debtag_list.append(1 if debtag in pkg_debtag else 0)

    return debtag_list


def main():
    axi = xapian.Database(XAPIAN_DATABASE_PATH)
    pkgs = get_pkgs_classification(linear_percent_function,
                                   sample_classification)

    debtags_name = get_debtags_name('tags.txt')

    debtag_classifications = []

    for key, value in pkgs.iteritems():
        debtags = get_pkg_debtags(axi, key)
        debtags = create_debtag_list(debtags_name, debtags)
        debtags.append(value)
        debtag_classifications.append(debtags)

    with open('pkg_classification.txt', 'wb') as text:
        pickle.dump(debtag_classifications, text)


if __name__ == "__main__":
    main()
