#! /usr/bin/env python
"""
    sample-popcon - extract a sample from popcon population
"""
__author__ = "Tassia Camoes Araujo <tassia@gmail.com>"
__copyright__ = "Copyright (C) 2011 Tassia Camoes Araujo"
__license__ = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import xapian
import os
import sys


def extract_sample(size, popcon, min_profile, max_profile, output):
    sample = []
    for n in range(1, popcon.get_doccount() + 1):
        user = popcon.get_document(n)
        pkgs_profile = [
            t.term for t in user.termlist() if t.term.startswith("XP")]
        print len(pkgs_profile)
        if(len(pkgs_profile) > min_profile and
           len(pkgs_profile) <= max_profile):
            sample.append(user.get_data())
        print n, len(sample)
        if len(sample) == size:
            break
    with open(("%s-%d-%d" % (output, min_profile, max_profile)), 'w') as f:
        for s in sample:
            f.write(s + '\n')

if __name__ == '__main__':
    popcon = xapian.Database(
        os.path.expanduser("~/.app-recommender/popcon_desktopapps"))
    print ("Popcon repository size: %d" % popcon.get_doccount())
    try:
        min_profile = int(sys.argv[1])
        max_profile = int(sys.argv[2])
        size = int(sys.argv[3])
    except:
        print "Usage: sample-popcon min_profile max_profile sample_size"
        exit(1)
    sample_file = "results/misc-popcon/sample"
    extract_sample(size, popcon, min_profile, max_profile, sample_file)
