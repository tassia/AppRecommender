#!/usr/bin/env python

import os
import commands

LOG_PATH = os.path.expanduser('~/app_recommender_log')
ALL_INSTALED_PKGS = LOG_PATH+"/all_pkgs.txt"
MANUAL_INSTALlED_PKGS_PATH = LOG_PATH + '/manual_installed_pkgs.txt'


def create_log_folder():

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH, 0755)


def create_file(file_path):

    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            os.utime(file_path, None)


def collect_manual_installed_pkgs():
    create_file(MANUAL_INSTALlED_PKGS_PATH)
    packages = commands.getoutput('apt-mark showmanual')

    with open(MANUAL_INSTALlED_PKGS_PATH, 'w') as text:
        text.write(packages)


def collect_all_user_pkgs():

    create_file(ALL_INSTALED_PKGS)
    dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')

    with open(ALL_INSTALED_PKGS, 'w') as pkgs:

        for pkg in dpkg_output.splitlines():
            pkg = pkg.split('\t')[0]
            pkgs.write(pkg+"\n")


def main():

    create_log_folder()
    collect_all_user_pkgs()
    collect_manual_installed_pkgs()


if __name__ == '__main__':
    main()
