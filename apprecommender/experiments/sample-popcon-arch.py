#! /usr/bin/env python
"""
    sample-popcon-arch - extract a sample of a specific arch
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
import sys

sys.path.insert(0, '../')

from user import RandomPopcon

if __name__ == '__main__':
    try:
        size = int(sys.argv[1])
        arch = sys.argv[2]
        popcon_dir = sys.argv[3]
        pkgs_filter = sys.argv[4]
    except:
        print "Usage: sample-popcon-arch size arch popcon_dir pkgs_filter"
        exit(1)

    sample_file = ("results/misc-popcon/sample-%s-%d" % (arch, size))
    with open(sample_file, 'w') as f:
        for n in range(1, size + 1):
            user = RandomPopcon(popcon_dir, arch, pkgs_filter)
            f.write(user.user_id + '\n')
            print "sample", n
