#!/usr/bin/env python

import argparse
import commands
import os
import shutil
import re

from apprecommender.config import Config
from apprecommender.main.app_recommender import AppRecommender


class AptRun:

    APT_FOLDER = os.path.join(Config().base_dir, "apt_run/")
    INSTALLED_PKGS_FILE = APT_FOLDER + "/installed_pkgs.txt"

    def enable(self):
        if not self.is_enable():
            os.makedirs(AptRun.APT_FOLDER)
            return True

        return False

    def disable(self):
        if self.is_enable():
            shutil.rmtree(AptRun.APT_FOLDER)
            return True

        return False

    def is_enable(self):
        return os.path.exists(AptRun.APT_FOLDER)

    def pre_install_pkgs(self):
        if self.is_enable():
            commands.getoutput("apt-mark showmanual > %s" %
                               AptRun.INSTALLED_PKGS_FILE)

    def post_invoke(self):
        if not self.is_enable():
            return

        with open(AptRun.INSTALLED_PKGS_FILE, 'r') as text:
            pre_installed_pkgs = set([line.strip() for line in text])

        pkgs = commands.getoutput("apt-mark showmanual").splitlines()
        pos_installed_pkgs = set([pkg.strip() for pkg in pkgs])

        installed_pkgs = list(pos_installed_pkgs - pre_installed_pkgs)

        self.make_recommendations(installed_pkgs)

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
                print '\nApprecommeder: The following packages are interesting'
                for pkg in pkgs:
                    print ' - {}'.format(pkg)


def get_args():
    aptrun_description = 'Integration of AppRecommender with apt'
    parser = argparse.ArgumentParser(description=aptrun_description)

    parser.add_argument(
        '--pre-install-pkgs',
        help='Indentify installed packages before install the new packages',
        action='store_true')

    parser.add_argument(
        '--post-invoke',
        help='Indentify the installed packages and makes recommendation',
        action='store_true')

    args = vars(parser.parse_args())

    return args


def main():
    args = get_args()
    apt_run = AptRun()

    if args['pre_install_pkgs']:
        apt_run.pre_install_pkgs()
    elif args['post_invoke']:
        apt_run.post_invoke()


if __name__ == '__main__':
    main()
