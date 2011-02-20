#!/usr/bin/python

#  AppRecomender - A GNU/Linux application recommender
#
#  Copyright (C) 2010  Tassia Camoes <tassia@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import commands
import re

import xapian
from debian import debtags

DB_PATH = "/var/lib/debtags/package-tags"
INDEX_PATH = os.path.expanduser("~/.app-recommender/debtags_index")

def load_debtags_db(path):
    """ Load debtags database. """
    debtags_db = debtags.DB()
    tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
    try:
        debtags_db.read(open(path, "r"), lambda x: not tag_filter.match(x))
    except IOError:
        print >> sys.stderr, ("IOError: could not open debtags file \'%s\'" %
                              path)
        exit(1)
    return debtags_db

def get_system_pkgs():
    """ Return set of system packages. """
    dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')
    return dpkg_output.replace('install','\t').split()

def get_most_relevant_tags(debtags_db,pkgs_list):
    """ Return most relevant tags considering a list of packages. """
    relevant_db = debtags_db.choose_packages(pkgs_list)
    relevance_index = debtags.relevance_index_function(debtags_db,relevant_db)
    sorted_relevant_tags = sorted(relevant_db.iter_tags(),
                                  lambda a, b: cmp(relevance_index(a),
                                                   relevance_index(b)))
    return normalize_tags(' '.join(sorted_relevant_tags[-50:]))

def normalize_tags(string):
    """ Normalize tag string so that it can be indexed and retrieved. """
    return string.replace(':','_').replace('-','\'')

def create_debtags_index(debtags_db,index_path):
    """ Create a xapian index for debtags info based on file 'debtags_db' and
    place it at 'index_path'.
    """
    if not os.path.exists(index_path):
        os.makedirs(index_path)
    print "Creating new debtags xapian index at \'%s\'" % index_path
    debtags_index = xapian.WritableDatabase(index_path,
                                            xapian.DB_CREATE_OR_OVERWRITE)
    for pkg,tags in debtags_db.iter_packages_tags():
        doc = xapian.Document()
        doc.set_data(pkg)
        for tag in tags:
            doc.add_term(normalize_tags(tag))
        print "indexing ",debtags_index.add_document(doc)
    return debtags_index

def load_debtags_index(debtags_db,reindex):
    """ Load an existing or new debtags index, based on boolean reindex. """
    if not reindex:
        try:
            print ("Opening existing debtags xapian index at \'%s\'" %
                   INDEX_PATH)
            debtags_index = xapian.Database(INDEX_PATH)
        except DatabaseError:
            print "Could not open debtags xapian index"
            reindex = 1
    if reindex:
        debtags_index = create_debtags_index(debtags_db,INDEX_PATH)
    return debtags_index


class PkgMatchDecider(xapian.MatchDecider):
    """ Extends xapian.MatchDecider to disconsider installed packages. """

    def __init__(self, installed_pkgs):
        xapian.MatchDecider.__init__(self)
        self.installed_pkgs = installed_pkgs

    def __call__(self, doc):
        return doc.get_data() not in self.installed_pkgs


if __name__ == '__main__':

    reindex = 0
    if len(sys.argv) == 2:
        DB_PATH = sys.argv[1]
        reindex = 1
        print "reindex true"
    elif len(sys.argv) > 2:
        print >> sys.stderr, ("Usage: %s [PATH_TO_DEBTAGS_DATABASE]" %
                              sys.argv[0])
        sys.exit(1)

    debtags_db = load_debtags_db(DB_PATH)
    installed_pkgs = get_system_pkgs()
    best_tags = get_most_relevant_tags(debtags_db,installed_pkgs)

    debtags_index = load_debtags_index(debtags_db,reindex)
    qp = xapian.QueryParser()
    query = qp.parse_query(best_tags)
    enquire = xapian.Enquire(debtags_index)
    enquire.set_query(query)

    mset = enquire.get_mset(0, 20, None, PkgMatchDecider(installed_pkgs))
    for m in mset:
        print "%2d: %s" % (m.rank, m.document.get_data())
