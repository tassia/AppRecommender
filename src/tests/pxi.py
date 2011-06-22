#!/usr/bin/env python
"""
    userTests - User class test case
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
import sys
sys.path.insert(0,'../')

class PkgXapianIndex(xapian.WritableDatabase):
    def __init__(self):
        xapian.WritableDatabase.__init__(self,".pxi",xapian.DB_CREATE_OR_OVERWRITE)
        pxi_file = open("package-xapian-index")
        for line in pxi_file:
            doc = xapian.Document()
            package_name = line.split()[0].rstrip(":")
            doc.add_term("XP"+package_name)
            package_tags = [tag.rstrip(",") for tag in line.split()[1:]]
            for tag in package_tags:
                doc.add_term("XT"+tag)
            self.add_document(doc)
