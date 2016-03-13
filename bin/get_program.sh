#!/usr/bin/env bash
#
# get_program.sh - get packages which have the tags 'role::program' associated

cat /var/lib/debtags/package-tags |grep "role::program" | awk -F: '{ print $1 }'
