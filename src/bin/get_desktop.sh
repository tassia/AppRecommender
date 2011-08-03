#!/usr/bin/env bash
cd /usr/share/app-install/desktop
sed -ne 's/X-AppInstall-Package=//p' * | sort -u
