#!/usr/bin/env bash
#
# get_desktop.sh - get packages which have desktop files
#
# DEPRECATED: use get_axipkgs.py to get this info from axi

cd /usr/share/app-install/desktop
sed -ne 's/X-AppInstall-Package=//p' * | sort -u | grep -v kdelibs | grep -v libfm-gtk0
