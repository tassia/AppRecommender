#!/usr/bin/env python

import os


LOG_PATH = '~/app_recommender_log'


def create_log_folder():
    os.mkdir(os.path.expanduser(LOG_PATH), 0755)


def main():
    create_log_folder()


if __name__ == '__main__':
    main()
