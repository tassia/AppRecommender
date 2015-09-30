#!/usr/bin/env python

import os
import commands
from subprocess import Popen, PIPE, STDOUT

from pkg_time_list import save_package_time, get_packages_time

LOG_PATH = os.path.expanduser('~/app_recommender_log')
ALL_INSTALLED_PKGS = LOG_PATH+"/all_pkgs.txt"
MANUAL_INSTALLED_PKGS_PATH = LOG_PATH + '/manual_installed_pkgs.txt'
PKGS_TIME_PATH = LOG_PATH + '/pkgs_time.txt'
HISTORY = LOG_PATH+"/user_history.txt"


def create_log_folder():

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH, 0755)


def create_file(file_path):

    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            os.utime(file_path, None)


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


def main():
    create_log_folder()
    collect_all_user_pkgs()
    collect_manual_installed_pkgs()
    collect_user_history()

    collect_pkgs_time()

if __name__ == '__main__':
    main()
