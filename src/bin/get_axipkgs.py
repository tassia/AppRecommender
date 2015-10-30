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

import sys
import getopt
sys.path.insert(0, '../')
import xapian
import logging
import logging.handlers

if __name__ == '__main__':
    short_options = "hdvo:p:t:"
    long_options = ["help", "path", "tag"]

    axi_tag = 'XP'
    axi_path = "/var/lib/apt-xapian-index/index"

    try:
        opts, args = getopt.getopt(sys.argv[1:], short_options,
                                   long_options)
    except getopt.GetoptError as error:
        logging.error("Bad syntax: %s" % str(error))
        sys.exit()

    for option, param in opts:
        if option in ("-h", "--help"):
            print "Usage: get_axipkgs"
            print " -h, --help \t Show this help"
            print " -p, --path \t Set axi_path, default is\
                  '/var/lib/apt-xapian-index/index'"
            print " -t, --tag \t Set axi_tag, exemple: XP, XT, Z. \
                  Default is XP"
            sys.exit()
        elif option in ("-p", "--path"):
            axi_path = param
        elif option in ("-t", "--tag"):
            axi_tag = param
        else:
            assert False, "unhandled option"

    axi = xapian.Database(axi_path)

    for n in range(1, axi.get_lastdocid()):
        doc = 0
        try:
            doc = axi.get_document(n)
        except:
            pass
        if doc:
            xp_terms = [t.term for t in doc.termlist()
                        if t.term.startswith(axi_tag)]
            if xp_terms:
                print xp_terms[0].lstrip(axi_tag)
