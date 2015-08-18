#!/usr/bin/env python
"""
    AppRecommender - A GNU/Linux application recommender
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

import os
import sys
sys.path.insert(0,'../')
import xapian

if __name__ == '__main__':

    axi_path = ""
    if len(sys.argv)<2:
        axi_path = "/var/lib/apt-xapian-index/index"
    elif sys.argv[1] == '-h':
        print "Usage: get_axipkgs index_path"
        print "If without index_path, the default is: /var/lib/apt-xapian-index/index"
        exit(1)
    else:
        axi_path = sys.argv[1]

    axi = xapian.Database(axi_path)

    for n in range(1,axi.get_lastdocid()):
        doc = 0
        try:
            doc = axi.get_document(n)
        except:
            pass
        if doc:
            xp_terms = [t.term for t in doc.termlist() if t.term.startswith("XP")]
            print xp_terms[0].lstrip('XP')
