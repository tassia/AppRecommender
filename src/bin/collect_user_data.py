#!/usr/bin/env python

import os
import commands
from subprocess import Popen, PIPE, STDOUT

from pkg_time_list import save_package_time, get_packages_time
from data_classification import get_alternative_pkg

LOG_PATH = os.path.expanduser('~/app_recommender_log')
ALL_INSTALLED_PKGS = LOG_PATH + '/all_pkgs.txt'
MANUAL_INSTALLED_PKGS_PATH = LOG_PATH + '/manual_installed_pkgs.txt'
PKGS_TIME_PATH = LOG_PATH + '/pkgs_time.txt'
HISTORY = LOG_PATH + '/user_history.txt'
PKGS_BINARY = LOG_PATH + '/pkgs_binary.txt'
POPCON_SUBMISSION = LOG_PATH + '/popcon-submission'


def create_log_folder():

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH, 0755)


def create_file(file_path):

    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            os.utime(file_path, None)


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
    create_file(MANUAL_INSTALLED_PKGS_PATH)
    packages = commands.getoutput('apt-mark showmanual')

    packages = [pkg for pkg in packages.splitlines()]

    with open(MANUAL_INSTALLED_PKGS_PATH, 'w') as text:
        for pkg in packages:
            text.write(pkg+'\n')


def collect_all_user_pkgs():
    create_file(ALL_INSTALLED_PKGS)
    dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')

    with open(ALL_INSTALLED_PKGS, 'w') as pkgs:
        for pkg in dpkg_output.splitlines():
            pkg = pkg.split('\t')[0]
            pkgs.write(pkg+"\n")


def collect_user_history():
    create_file(HISTORY)
    shell_command = 'bash -i -c "history -r; history"'
    proc = Popen(shell_command, shell=True, stdin=PIPE, stdout=PIPE,
                 stderr=STDOUT, close_fds=True)
    history_output = proc.stdout.read()

    with open(HISTORY, 'w') as history:
        for command in history_output.splitlines():
            history.write(command.split('  ')[1] + '\n')


def collect_pkgs_time():
    manual_pkgs = []
    with open(MANUAL_INSTALLED_PKGS_PATH, 'r') as text:
        manual_pkgs = [line.strip() for line in text]

    pkgs_time = get_packages_time(manual_pkgs)

    save_package_time(pkgs_time, PKGS_TIME_PATH)


def collect_pkgs_binary():
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


def main():
    print "Creating log folder"
    create_log_folder()

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
