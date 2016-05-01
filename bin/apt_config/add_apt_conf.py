#!/usr/bin/python

import os
import sys

sys.path.insert(0, "{0}/../../".format(os.path.dirname(__file__)))


APT_FOLDER = "/home/%s/.app-recommender/apt_conf" % os.getenv("SUDO_USER")
APT_CONF_FILE = '/etc/apt/apt.conf.d/99app-recommender'

FILES_FOLDER = os.path.dirname(os.path.abspath(__file__))
POST_INVOKE_PATH = FILES_FOLDER + "/post_invoke.py"
PRE_INSTALL_PKGS_PATH = FILES_FOLDER + "/pre_install_pkgs.py"

INSTALLED_PKGS_FILE = APT_FOLDER + "/installed_pkgs.txt"


def main():
    post_invoke = 'DPkg::Post-Invoke {"python %s";};' % POST_INVOKE_PATH
    pre_install_pkgs = ('DPkg::Pre-Install-Pkgs {"python %s";};' %
                        PRE_INSTALL_PKGS_PATH)

    print("Creating folder: {}".format(APT_FOLDER))
    if not os.path.exists(APT_FOLDER):
        os.makedirs(APT_FOLDER)

    print("Creating file: {}".format(APT_CONF_FILE))
    with open(APT_CONF_FILE, 'w') as text:
        text.write(post_invoke)
        text.write('\n')
        text.write(pre_install_pkgs)
        text.write('\n')

if __name__ == "__main__":
    main()
