#!/usr/bin/env python

import apt
import os
import logging
import commands
import sys

sys.path.insert(0, '../')
sys.path.insert(0, '../../')

from subprocess import Popen, PIPE
from pkg_time_list import save_package_time, get_packages_time
from data_classification import get_alternative_pkg
from app_recommender import AppRecommender

LOG_PATH = os.path.expanduser('~/app_recommender_log')
ALL_INSTALLED_PKGS = LOG_PATH + '/all_pkgs.txt'
MANUAL_INSTALLED_PKGS_PATH = LOG_PATH + '/manual_installed_pkgs.txt'
PKGS_TIME_PATH = LOG_PATH + '/pkgs_time.txt'
HISTORY = LOG_PATH + '/user_history.txt'
PKGS_BINARY = LOG_PATH + '/pkgs_binary.txt'
RECOMMENDATION_PATH = LOG_PATH + '/{0}_recommendation.txt'
USER_PREFERENCES = LOG_PATH + '/user_preferences.txt'
POPCON_SUBMISSION = LOG_PATH + '/popcon-submission'
PC_INFORMATIONS = LOG_PATH + '/pc_informations.txt'


PKGS_DEPENDENCIES = []


def create_log_folder():
    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH, 0755)


def create_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            os.utime(file_path, None)
        return True

    return False


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def save_list(list_to_save, file_path):
    delete_file(file_path)
    create_file(file_path)

    with open(file_path, 'w') as text:
        for element in list_to_save:
            text.write(str(element) + '\n')


def rename_file(original_name, new_name):
    os.rename(original_name, new_name)


def get_submission_id(submission_header):

    fields = submission_header.split(' ')
    return fields[2][3:]


def collect_popcon_submission():
    popcon = Popen('./popularity-contest',
                   shell=True, stdin=PIPE,
                   stdout=PIPE,
                   stderr=PIPE)

    popcon_output = popcon.stdout.read()

    popcon_parse = popcon_output.splitlines()
    submission_id = get_submission_id(popcon_parse[0])

    submission = [line for line in popcon_parse]

    save_list(submission, POPCON_SUBMISSION)

    rename_file(POPCON_SUBMISSION, LOG_PATH+"/"+submission_id)


def collect_manual_installed_pkgs():
    if create_file(MANUAL_INSTALLED_PKGS_PATH):
        packages = commands.getoutput('apt-mark showmanual')

        packages = [pkg for pkg in packages.splitlines()]

        save_list(packages, MANUAL_INSTALLED_PKGS_PATH)


def collect_all_user_pkgs():
    if create_file(ALL_INSTALLED_PKGS):
        packages = get_all_user_pkgs()
        save_list(packages, ALL_INSTALLED_PKGS)


def collect_pkgs_time():
    if create_file(PKGS_TIME_PATH):
        manual_pkgs = []
        with open(MANUAL_INSTALLED_PKGS_PATH, 'r') as text:
            manual_pkgs = [line.strip() for line in text]

        pkgs_time = get_packages_time(manual_pkgs)

        save_package_time(pkgs_time, PKGS_TIME_PATH)


def collect_pkgs_binary():
    if create_file(PKGS_BINARY):
        pkgs = []
        pkgs_binary = {}

        with open(ALL_INSTALLED_PKGS, 'r') as text:
            pkgs = [line.strip() for line in text]

        for pkg in pkgs:
            pkg_binary = get_pkg_binary(pkg)
            if pkg_binary:
                pkgs_binary[pkg] = pkg_binary

        write_text = "{0} {1}"

        formated_list = [write_text.format(pkg, binary)
                         for pkg, binary in pkgs_binary.iteritems()]

        save_list(formated_list, PKGS_BINARY)


def get_pkg_binary(pkg):
    stat_command = "stat `which {0}`".format(pkg)
    stat_success = "File:"
    pkg_bin = commands.getoutput(stat_command.format(pkg))

    if stat_success in pkg_bin:
        return pkg

    return get_alternative_pkg(pkg)


def get_pkgs_of_recommendation(recommendation_size, strategy,
                               no_auto_pkg_profile):
    app_recommender = AppRecommender()

    app_recommender.recommender.set_strategy(strategy)
    recommender = (app_recommender.make_recommendation(recommendation_size,
                                                       no_auto_pkg_profile))
    pkgs = [pkg.split(':')[1][1:]
            for pkg in str(recommender).splitlines()[1:]]

    return pkgs


def collect_user_preferences():
    recommendation_size = 5
    no_auto_pkg_profile = True

    recommendations = {}

    recommendations['cb'] = (get_pkgs_of_recommendation(recommendation_size,
                             'cb', no_auto_pkg_profile))
    recommendations['cbt'] = (get_pkgs_of_recommendation(recommendation_size,
                              'cbt', no_auto_pkg_profile))

    all_recommendations = set(sum(recommendations.values(), []))
    all_recommendations = sorted(list(all_recommendations))

    index = 0
    user_preferences = {}
    all_rec_len = len(all_recommendations)

    print "rank a package recommendation with 0-10"

    message = "\n\nPackage [{0}/{1}] - {2} \n"
    message += "Description: {3}\n"
    message += "Rank: "

    for pkg in all_recommendations:
        pkg_description = apt.Cache()[pkg].versions[0].description
        rank = raw_input(message.format((index+1), all_rec_len, pkg,
                                        pkg_description))
        rank = int(rank)
        user_preferences[pkg] = rank
        index += 1

    preferences_list = ["{0}:{1}".format(pkg, user_preferences[pkg])
                        for pkg in all_recommendations]

    for rec_key, rec_value in recommendations.iteritems():
        save_list(rec_value, RECOMMENDATION_PATH.format(rec_key))

    save_list(preferences_list, USER_PREFERENCES)


def get_all_user_pkgs():
    dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')

    packages = [pkg.split('\t')[0] for pkg in dpkg_output.splitlines()
                if 'deinstall' not in pkg.split('\t')[-1]]

    return packages


def get_uninstalled_dependencies():
    user_pkgs = []
    unistalled_pkgs = []

    user_pkgs = get_all_user_pkgs()

    for pkg in PKGS_DEPENDENCIES:
        if pkg not in user_pkgs:
            unistalled_pkgs.append(pkg)

    return unistalled_pkgs


def check_dependencies():
    unistalled_pkgs = get_uninstalled_dependencies()
    unistalled_dependencies = ''

    if len(unistalled_pkgs) > 0:
        unistalled_dependencies = ''.join(str(pkg)+' '
                                          for pkg in unistalled_pkgs)

    return unistalled_dependencies


def collect_pc_informations():
    informations = []
    linux_kernel_version = commands.getoutput('uname -s -r')

    distribution_version = commands.getoutput('lsb_release -a')
    distribution_version = distribution_version.splitlines()

    informations.append(linux_kernel_version)
    informations.extend(distribution_version)

    save_list(informations, PC_INFORMATIONS)


def main():
    logging.getLogger().disabled = True

    # print "Checking dependencies"
    # unistalled_dependencies = check_dependencies()
    # if len(unistalled_dependencies) > 0:
    #     print 'These packages need to be installed:', unistalled_dependencies
    #     return

    print "Creating log folder"
    create_log_folder()

    print "Collecting user preferences"
    collect_user_preferences()

    print "Collecting PC informations"
    collect_pc_informations()

    print "Collecting all user packages"
    collect_all_user_pkgs()

    print "Collecting manual installed packages"
    collect_manual_installed_pkgs()

    print "Collecting packages time"
    collect_pkgs_time()

    print "Collecting packages binary"
    collect_pkgs_binary()

    print "Collecting popularity-contest submission"
    collect_popcon_submission()


if __name__ == '__main__':
    main()
