#!/usr/bin/python

import commands

from add_apt_conf import INSTALLED_PKGS_FILE


def main():
    commands.getoutput("apt-mark showmanual > {}".format(INSTALLED_PKGS_FILE))


if __name__ == "__main__":
    main()
