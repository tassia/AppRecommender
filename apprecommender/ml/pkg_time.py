import os
import re
import commands

from apprecommender.data_classification import get_time_from_package
from apprecommender.config import Config
from apprecommender.user import LocalSystem

USER_DATA_DIR = Config().user_data_dir


class PkgTime:

    def __init__(self):
        pass

    def create_pkg_data(self):
        user = LocalSystem()
        user_pkgs = user.pkg_profile

        pkgs_time = self.get_packages_time(user_pkgs)
        self.save_package_time(pkgs_time)
        return pkgs_time

    def get_best_time(self, pkg):
        valid_regex = re.compile(
            r'/usr/bin/|/usr/sbin|/usr/game/|/usr/lib/.+/')
        pkg_files = commands.getoutput('dpkg -L {}'.format(pkg))

        bestatime, bestmtime = 0, 0
        for pkg_file in pkg_files.splitlines():
            if valid_regex.search(pkg_file):
                access, modify = get_time_from_package(pkg_file, pkg_bin=False)

                if access >= bestatime:
                    bestatime = access
                    bestmtime = modify

        return (bestmtime, bestatime)

    def get_package_data(self, file_path=USER_DATA_DIR + 'pkg_data.txt'):
        if os.path.isfile(file_path):
            pkgs_time = {}

            with open(file_path, 'r') as pkg_data:
                for pkg_line in pkg_data:
                    name, modify, access = pkg_line.split(' ')
                    pkgs_time[name] = [modify, access]

            return pkgs_time

        else:
            return self.create_pkg_data()

    def get_packages_time(self, pkgs, verbose=False):
        pkgs_time = {}

        for pkg in pkgs:
            modify, access = self.get_best_time(pkg)

            if modify and access:
                if verbose:
                    print 'ADD: {}'.format(pkg)

                pkgs_time[pkg] = []
                pkgs_time[pkg].append(modify)
                pkgs_time[pkg].append(access)
            else:
                if verbose:
                    print 'NOT: {} {} {}'.format(pkg, modify, access)

        return pkgs_time

    def print_package_time(self, pkgs_time):
        for key, value in pkgs_time.iteritems():
            print "{} : Modify {}, Access {}".format(key, value[0], value[1])

    def save_package_time(self, pkgs_time,
                          file_path=USER_DATA_DIR + 'pkg_data.txt'):
        with open(file_path, 'w') as pkg_data:
            pkg_str = "{pkg} {modify} {access}\n"

            for pkg, times in pkgs_time.iteritems():
                pkg_line = pkg_str.format(pkg=pkg, modify=times[0],
                                          access=times[1])
                pkg_data.write(pkg_line)
