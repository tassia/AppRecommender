#!/usr/bin/python

import os
import shutil

from add_apt_conf import APT_FOLDER, APT_CONF_FILE


def main():
    os.remove(APT_CONF_FILE)
    shutil.rmtree(APT_FOLDER)

if __name__ == "__main__":
    main()
