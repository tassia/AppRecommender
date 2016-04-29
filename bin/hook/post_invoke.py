#!/usr/bin/python

import commands

from add_apt_conf import INSTALLED_PKGS_FILE


def main():
    with open(INSTALLED_PKGS_FILE, 'r') as text:
        pre_installed_pkgs = set([line.strip() for line in text])

    pkgs = commands.getoutput("apt-mark showmanual")
    pos_installed_pkgs = set([line.strip() for line in pkgs.splitlines()])

    installed_pkgs = list(pos_installed_pkgs - pre_installed_pkgs)

    if len(installed_pkgs) > 0:
        print("\n\n")
        print("installed packages: {}".format(installed_pkgs))
        print("\n\n")


if __name__ == "__main__":
    main()
