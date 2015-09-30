#!/usr/bin/env python

import os


LOG_PATH = os.path.expanduser('~/app_recommender_log')


def create_log_folder():

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH, 0755)

def create_file(file_path):

    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            os.utime(file_path, None)

def main():

    create_log_folder()
    create_file(LOG_PATH+"/all_pkgs.txt")


if __name__ == '__main__':
    main()
