#!/usr/bin/env python

import os
import logging
import commands
import sys

sys.path.insert(0, '../')

from subprocess import Popen, PIPE, STDOUT
from pkg_time_list import save_package_time, get_packages_time
from data_classification import get_alternative_pkg
from app_recommender import AppRecommender

LOG_PATH = os.path.expanduser('~/app_recommender_log')
ALL_INSTALLED_PKGS = LOG_PATH + '/all_pkgs.txt'
MANUAL_INSTALLED_PKGS_PATH = LOG_PATH + '/manual_installed_pkgs.txt'
PKGS_TIME_PATH = LOG_PATH + '/pkgs_time.txt'
HISTORY = LOG_PATH + '/user_history.txt'
PKGS_BINARY = LOG_PATH + '/pkgs_binary.txt'
OLD_RECOMMENDATION = LOG_PATH + '/old_rec.txt'
NEW_RECOMMENDATION = LOG_PATH + '/new_rec.txt'
USER_PREFERENCES = LOG_PATH + '/user_preferences.txt'
POPCON_SUBMISSION = LOG_PATH + '/popcon-submission'


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


def save_pkg_list(pkgs, file_path):
    delete_file(file_path)
    create_file(file_path)

    with open(file_path, 'w') as text:
        for pkg in pkgs:
            text.write(str(pkg) + '\n')


def rename_file(original_name, new_name):
    os.rename(original_name, new_name)


def get_submission_id(submission_header):

    fields = submission_header.split(' ')
    return fields[2][3:]


def collect_popcon_submission():
    popcon = Popen('sudo /usr/sbin/popularity-contest',
                   shell=True, stdin=PIPE,
                   stdout=PIPE,
                   stderr=PIPE)

    popcon_output = popcon.stdout.read()

    with open(POPCON_SUBMISSION, 'w') as submission:
        popcon_parse = popcon_output.splitlines()
        submission_id = get_submission_id(popcon_parse[0])

        for line in popcon_parse:
            submission.write(line+"\n")

    rename_file(POPCON_SUBMISSION, LOG_PATH+"/"+submission_id)


def collect_manual_installed_pkgs():
    if create_file(MANUAL_INSTALLED_PKGS_PATH):
        packages = commands.getoutput('apt-mark showmanual')

        packages = [pkg for pkg in packages.splitlines()]

        save_pkg_list(packages, MANUAL_INSTALLED_PKGS_PATH)


def collect_all_user_pkgs():
    if create_file(ALL_INSTALLED_PKGS):
        dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')

        with open(ALL_INSTALLED_PKGS, 'w') as pkgs:
            for pkg in dpkg_output.splitlines():
                pkg = pkg.split('\t')[0]
                pkgs.write(pkg+"\n")


def collect_user_history():
    if create_file(HISTORY):
        shell_command = 'bash -i -c "history -r; history"'
        proc = Popen(shell_command, shell=True, stdin=PIPE, stdout=PIPE,
                     stderr=STDOUT, close_fds=True)
        history_output = proc.stdout.read()

        with open(HISTORY, 'w') as history:
            for command in history_output.splitlines():
                history.write(command.split('  ')[1] + '\n')


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
            binary = get_pkg_binary(pkg)
            if binary:
                pkgs_binary[pkg] = binary

        write_text = "{pkg} {binary}\n"
        with open(PKGS_BINARY, 'w') as text:
            for pkg, binary in pkgs_binary.iteritems():
                text.write(write_text.format(pkg=pkg, binary=binary))


def get_pkg_binary(pkg):
    stat_command = "stat `which {0}`".format(pkg)
    stat_success = "File:"
    pkg_bin = commands.getoutput(stat_command.format(pkg))

    if stat_success in pkg_bin:
        return pkg

    return get_alternative_pkg(pkg)


def get_pkgs_of_recommendation(recommendation_size, no_auto_pkg_profile,
                               option):
    app_recommender = AppRecommender()

    recommender = (app_recommender.make_recommendation(recommendation_size,
                   no_auto_pkg_profile, option))
    pkgs = [pkg.split(':')[1][1:] for pkg in str(recommender).splitlines()[1:]]

    return pkgs


def collect_user_preferences():
    recommendation_size = 5
    no_auto_pkg_profile = True

    old_rec = get_pkgs_of_recommendation(recommendation_size,
                                         no_auto_pkg_profile, 0)
    new_rec = get_pkgs_of_recommendation(recommendation_size,
                                         no_auto_pkg_profile, 1)

    all_rec = sorted(list(set(old_rec) | set(new_rec)))

    index = 0
    user_preferences = {}
    all_rec_len = len(all_rec)

    print "rank a package recommendation with 0-10"

    message = "[{0}/{1}] - {2} , rank: "
    for pkg in all_rec:
        rank = raw_input(message.format((index+1), all_rec_len, pkg))
        rank = int(rank)
        user_preferences[pkg] = rank
        index += 1

    preferences_list = ["{0}:{1}".format(pkg, user_preferences[pkg])
                        for pkg in all_rec]

    save_pkg_list(old_rec, OLD_RECOMMENDATION)
    save_pkg_list(new_rec, NEW_RECOMMENDATION)
    save_pkg_list(preferences_list, USER_PREFERENCES)


def main():
    logging.getLogger().disabled = True

    print "Creating log folder"
    create_log_folder()

    print "Collecting user preferences"
    collect_user_preferences()

    print "Collecting all user packages"
    collect_all_user_pkgs()

    print "Collecting manual installed packages"
    collect_manual_installed_pkgs()

    print "Collecting user history"
    collect_user_history()

    print "Collecting packages time"
    collect_pkgs_time()

    print "Collecting packages binary"
    collect_pkgs_binary()

    print "Collecting popularity-contest submission"
    collect_popcon_submission()


if __name__ == '__main__':
    main()
