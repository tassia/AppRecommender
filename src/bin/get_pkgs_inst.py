#!/usr/bin/env python
#
# get_pkgs_inst.py - get tuple (package,installation) from popcon results file

from operator import itemgetter
if __name__ == '__main__':
    pkgs_inst = {}
    with open("/root/org/popcon.debian.org/popcon-mail/results") as results:
        for line in results:
            if line.startswith("Package"):
                fields = line.split()
                inst = int(fields[2])+int(fields[3])+int(fields[4])
                if inst > 20:
                    pkgs_inst[fields[1]] = inst
    sorted_by_inst = sorted(pkgs_inst.items(), key=itemgetter(1))
    for pkg, inst in sorted_by_inst:
        print pkg, inst
