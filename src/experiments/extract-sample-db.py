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
import random
import sys

if __name__ == '__main__':
    try:
        sample_file = sys.argv[1]
    	popcon = xapian.WritableDatabase(sys.argv[2],xapian.DB_OPEN)
    except:
        print "Usage: extract-sample-db sample_file popcon_index"
        exit(1)
    enquire = xapian.Enquire(popcon)
    print sample_file.split("/")
    new_popcon = xapian.WritableDatabase(sys.argv[2]+"-"+sample_file.split("/")[-1],xapian.DB_CREATE_OR_OVERWRITE)
    print ("Popcon repository size: %d" % popcon.get_doccount())
    for submission in open(sample_file):
        print "ID"+submission.strip()
        query = xapian.Query("ID"+submission.strip())
        enquire.set_query(query)
        mset = enquire.get_mset(0,20)
        for m in mset:
            print "Adding doc %s"%m.docid
            new_popcon.add_document(popcon.get_document(m.docid))
            print "Removing doc %s"%m.docid
            popcon.delete_document(m.docid)
    print ("Popcon repository size: %d" % popcon.get_doccount())
    print ("Popcon repository size: %d" % new_popcon.get_doccount())
