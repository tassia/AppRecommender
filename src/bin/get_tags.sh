#!/usr/bin/env bash
cat /var/lib/debtags/vocabulary | grep "Tag:" | egrep -v "culture::|devel::lang|hardware::|implemented-in::|interface::|iso15924::|made-of::|network::|protocol::|role::|scope::|secteam::|special::|uitoolkit::|x11::|TODO" | awk '{print $2}'
