#!/usr/bin/env python

import argparse
import os
import shutil
import re

from apprecommender.config import Config
from apprecommender.main.app_recommender import AppRecommender
from apprecommender.user import LocalSystem


class AptRun:

    def __init__(self):
        apt_folder = os.path.join(Config().base_dir, "apt_run/")
        self.set_folder(apt_folder)

    def set_folder(self, folder_path):
        folder_path = os.path.expanduser(folder_path)
        folder_path = os.path.abspath(folder_path)

        if folder_path[-1] != '/':
            folder_path += '/'

        self.apt_folder = folder_path
        self.installed_pkgs_file = self.apt_folder + "installed_pkgs.txt"

    def enable(self):
        if not self.is_enable():
            os.makedirs(self.apt_folder)
            return True

        return False

    def disable(self):
        if self.is_enable():
            shutil.rmtree(self.apt_folder)
            return True

        return False

    def is_enable(self):
        return os.path.exists(self.apt_folder)

    def get_user_pkgs(self):
        user = LocalSystem()
        user_pkgs = user.pkg_profile

        return user_pkgs

    def pre_install_pkgs(self):
        if self.is_enable():
            user_pkgs = self.get_user_pkgs()
            with open(self.installed_pkgs_file, 'w') as text:
                text.write("\n".join(user_pkgs))

    def post_invoke(self):
        if not self.is_enable():
            return []

        with open(self.installed_pkgs_file, 'r') as text:
            pre_installed_pkgs = set([line.strip() for line in text])

        pkgs = self.get_user_pkgs()
        pos_installed_pkgs = set([pkg.strip() for pkg in pkgs])

        installed_pkgs = list(pos_installed_pkgs - pre_installed_pkgs)

        return installed_pkgs

    def get_recommendation_pkgs(self, installed_pkgs):
        app_recommender = AppRecommender()

        app_recommender.recommender.set_strategy('cbpkg')
        rec = app_recommender.make_recommendation(
            reference_pkgs=installed_pkgs, print_recommendation=False)

        pkgs_regex = re.compile(r'^\d:\s([^\s]+)', re.MULTILINE)
        pkgs = pkgs_regex.findall(rec.__str__())

        return pkgs

    def make_recommendations(self, installed_pkgs):
        if len(installed_pkgs) > 0:
            pkgs = self.get_recommendation_pkgs(installed_pkgs)
            if len(pkgs) > 0:
                print '\nApprecommeder: The following packages are' \
                      ' interesting'
                for pkg in pkgs:
                    print ' - {}'.format(pkg)


def get_args():
    aptrun_description = 'Integration of AppRecommender with apt'
    parser = argparse.ArgumentParser(description=aptrun_description)

    parser.add_argument(
        '--pre-install-pkgs',
        help='Identify installed packages before install the new packages',
        action='store_true')

    parser.add_argument(
        '--post-invoke',
        help='Identify the installed packages and makes recommendation',
        action='store_true')

    args = vars(parser.parse_args())

    return args


def main():
    args = get_args()
    apt_run = AptRun()

    if args['pre_install_pkgs']:
        apt_run.pre_install_pkgs()
    elif args['post_invoke']:
        installed_pkgs = apt_run.post_invoke()
        apt_run.make_recommendations(installed_pkgs)


if __name__ == '__main__':
    main()
