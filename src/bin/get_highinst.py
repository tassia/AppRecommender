#!/usr/bin/env python

if __name__ == '__main__':
    with open("/root/org/popcon.debian.org/popcon-mail/results") as results:
        for line in results.readlines():
            if line.startswith("Package"):
                fields = line.split()
                inst = int(fields[2])+int(fields[3])+int(fields[4])
                if inst > 20:
                    print fields[1], inst
