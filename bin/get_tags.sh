#!/usr/bin/env bash
#
# get_tags.py - get meaningful tags for recommendation purposes

cat /var/lib/debtags/vocabulary | grep "Tag:" | egrep -v "culture::|devel::lang|hardware::|implemented-in::|interface::|iso15924::|made-of::|network::|protocol::|role::|scope::|secteam::|special::|uitoolkit::|x11::|TODO" | awk '{print $2}'
