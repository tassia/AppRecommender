#!/usr/bin/env python
#
# get_pkgs_inst.py - get tuple (package,installation) from popcon results file
#
# results_file: org/popcon.debian.org/popcon-mail/results

import sys
from operator import itemgetter

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: get_pkgs_inst popcon_results_path"
        exit(1)

    results_path = sys.argv[1]
    pkgs_inst = {}
    with open(results_path) as results:
        for line in results:
            if line.startswith("Package"):
                fields = line.split()
                inst = int(fields[2]) + int(fields[3]) + int(fields[4])
                pkgs_inst[fields[1]] = inst
    sorted_by_inst = sorted(pkgs_inst.items(), key=itemgetter(1))
    for pkg, inst in sorted_by_inst:
        print pkg, inst
