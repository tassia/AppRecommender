#!/usr/bin/python

import os
import sys
sys.path.insert(0, '../')

from config import Config

USER_DATA_DIR = Config().user_data_dir


def main():
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)

    print("\n - Generating packages time list")
    os.system("./pkg_time_list.py")

    print("\n - Generating debtags")
    os.system("./get_axipkgs.py -t XT > {0}tags.txt".format(USER_DATA_DIR))

    print("\n - Making machine learning traning")
    os.system("./pkg_classification.py")

if __name__ == '__main__':
    main()
