#!/usr/bin/env python

import commands
import calendar
import math
import time


pkgs_times = {}
pkgs_time_weight = {}
best_weight_terms = {}


def get_time_from_package(pkg):

    if pkg in pkgs_times:
        modify, access = pkgs_times[pkg]
    else:
        modify = get_time('Y', pkg)
        access = get_time('X', pkg)
        pkgs_times[pkg] = [modify, access]

    return pkgs_times[pkg]


def get_alternative_pkg(pkg):

    dpkg_command = "dpkg -L {0}| grep /usr/bin/"
    dpkg_command += " || dpkg -L {0}| grep /usr/sbin/"
    bin_path = '/usr/bin'
    pkg_bin = commands.getoutput(dpkg_command.format(pkg))

    for pkg_path in pkg_bin.splitlines():

        if bin_path in pkg_path:
            return pkg_path
        elif pkg in pkg_path:
            return pkg_path

    return None


def get_time(option, pkg):
    stat_base = "stat -c '%{option}' `which {package}`"
    stat_error = 'stat: missing operand'
    stat_time = stat_base.format(option=option, package=pkg)

    pkg_time = commands.getoutput(stat_time)

    if not pkg_time.startswith(stat_error):
        pkgs_times[pkg] = pkg_time
        return pkg_time

    return None


def linear_percent_function(modify, access, time_now):
    modify, access = int(modify), int(access)

    time_access = access - modify
    time_actual = time_now - modify

    percent = float(time_access) / float(time_actual)

    return percent


def get_pkg_time_weight(pkg):
    modify, access = get_time_from_package(pkg)

    if not modify and not access:
        modify, access = get_time_from_package(get_alternative_pkg(pkg))

    if not modify and not access:
        return 0

    time_now = calendar.timegm(time.gmtime())

    return linear_percent_function(modify, access, time_now)


def calculate_time_curve(pkg_time_weight):

    if not pkg_time_weight:
        return 0

    lambda_value = 1

    return 1/math.exp((1 - pkg_time_weight)*lambda_value)


def time_weight(term, term_list):
    weight = []
    weight_len = 5
    weight_delta = 0.5

    for pkg in term_list:
        if pkg in pkgs_time_weight:
            weight += pkgs_time_weight[pkg]
        else:
            pkg_time_weight = get_pkg_time_weight(pkg)
            pkgs_time_weight[pkg] = pkg_time_weight
            weight.append(calculate_time_curve(pkg_time_weight))

    if len(weight) < weight_len:
        for i in range(len(weight), weight_len):
            weight.append(weight[-1] - weight_delta)

    time_weight = float(sum(weight[0:weight_len])) / float(weight_len)

    best_weight_terms[term] = time_weight

    return time_weight


def print_best_weight_terms(terms_package):
    index = 0
    print "BEST TERMS"

    with open('package.txt', 'w') as text:
        for key, value in terms_package.iteritems():
            pkgs = ""
            for pkg in value:
                pkgs += pkg
                pkgs += ","

            text.write("{0}: {1}\n".format(key, pkgs))

    for term in sorted(best_weight_terms, key=best_weight_terms.get,
                       reverse=True):
        if index < 10:
            print "\n"
            print term, best_weight_terms[term]
            print '-'

            for pkg in terms_package[term]:
                print "[{0}: {1} {2}]\n".format(pkg, get_pkg_time_weight(pkg),
                                                get_alternative_pkg(pkg))

        index += 1
