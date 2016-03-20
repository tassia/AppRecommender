import commands
import re

from os import path

from src.data_classification import get_time_from_package, get_alternative_pkg
from src.config import Config

USER_DATA_DIR = Config().user_data_dir


def create_pkg_data():
    manual_pkgs = get_packages_from_apt_mark()
    pkgs_time = get_packages_time(manual_pkgs)
    save_package_time(pkgs_time)
    return pkgs_time


def get_package_data(file_path=USER_DATA_DIR + 'pkg_data.txt'):

    if path.isfile(file_path):
        pkgs_time = {}

        with open(file_path, 'r') as pkg_data:
            for pkg_line in pkg_data:
                name, modify, access = pkg_line.split(' ')
                pkgs_time[name] = [modify, access]

        return pkgs_time

    else:
        return create_pkg_data()


def get_packages_time(pkgs):
    pkgs_time = {}

    for pkg in pkgs:

        modify, access = get_time_from_package(pkg)

        if not modify or not access:
            pkg_tmp = get_alternative_pkg(pkg)
            modify, access = get_time_from_package(pkg_tmp)

        if modify and access:
            pkgs_time[pkg] = []
            pkgs_time[pkg].append(modify)
            pkgs_time[pkg].append(access)

    return pkgs_time


def print_package_time(pkgs_time):
    for key, value in pkgs_time.iteritems():
        print "{0} : Modify {1}, Access {2}".format(key, value[0], value[1])


def save_package_time(pkgs_time, file_path=USER_DATA_DIR + 'pkg_data.txt'):
    with open(file_path, 'w') as pkg_data:

        pkg_str = "{pkg} {modify} {access}\n"
        for pkg, times in pkgs_time.iteritems():

            pkg_line = pkg_str.format(pkg=pkg, modify=times[0],
                                      access=times[1])
            pkg_data.write(pkg_line)


def get_packages_from_apt_mark():
    dpkg_output = commands.getoutput('apt-mark showmanual')
    pkgs = []

    for pkg in dpkg_output.splitlines():

        if not re.match(r'^lib', pkg):
            pkgs.append(pkg)

    return pkgs
