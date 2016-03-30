#!/usr/bin/python

import os
import sys

sys.path.insert(0, "{0}/../".format(os.path.dirname(__file__)))

import src.ml.pkg_time as pkg_time


def main():
    manual_pkgs = pkg_time.get_packages_from_apt_mark()
    print "Size of manual installed packages apt-mark:", len(manual_pkgs)

    pkgs_time = pkg_time.get_packages_time(manual_pkgs)
    pkg_time.print_package_time(pkgs_time)

    print "\nSize of dictionary:", len(pkgs_time)
    pkg_time.save_package_time(pkgs_time)


if __name__ == "__main__":
    main()
