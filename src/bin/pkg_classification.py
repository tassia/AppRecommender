#!/usr/bin/python

import time
import calendar


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

    with open('pkg_data.txt') as pkg_data:
        for pkg_line in pkg_data:
            name, modify, access = pkg_line.split(' ')

            percent = percent_function(modify, access, time_now)

            pkgs[name] = classification_function(percent)

    return pkgs


if __name__ == "__main__":
    pkgs = get_pkgs_classification(linear_percent_function,
                                   sample_classification)

    for pkg, label in pkgs.iteritems():
        print "{pkg} {label}".format(pkg=pkg, label=label)
