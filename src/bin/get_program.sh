#!/usr/bin/env bash
cat /var/lib/debtags/package-tags |grep "role::program" | awk -F: '{ print $1 }'
