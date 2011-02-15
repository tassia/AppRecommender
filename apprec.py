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

import xapian
from debian import debtags
import re
import sys
import os
import commands

DB_PATH = "/var/lib/debtags/package-tags"
INDEX_PATH = "~/.app-recommender/debtags_index"

INDEX_PATH = os.path.expanduser(INDEX_PATH)

def normalize_tags(string):
    return string.replace(':','_').replace('-','\'')

def createDebtagsIndex(debtags_db,index_path):
    if not os.path.exists(index_path):
        os.makedirs(index_path)
    print "Creating new debtags xapian index at \'%s\'" % index_path
    debtags_index = xapian.WritableDatabase(index_path, xapian.DB_CREATE_OR_OVERWRITE)
    for pkg,tags in debtags_db.iter_packages_tags():
        doc = xapian.Document()
        doc.set_data(pkg)
        for tag in tags:
            doc.add_term(normalize_tags(tag))
        print "indexing ",debtags_index.add_document(doc)
    return debtags_index

# MatchDecider to disconsider installed packages
class pkgmatchdecider(xapian.MatchDecider):
    def __init__(self, installed_pkgs):
        xapian.MatchDecider.__init__(self)
        self.installed_pkgs = installed_pkgs

    def __call__(self, doc):
        return doc.get_data() not in self.installed_pkgs

# Handle input arguments
REINDEX = 0
if len(sys.argv) == 2:
    DB_PATH = sys.argv[1]
    REINDEX = 1
    print "REINDEX true"
elif len(sys.argv) > 2:
    print >> sys.stderr, "Usage: %s [PATH_TO_DEBTAGS_DATABASE]" % sys.argv[0]
    sys.exit(1)

# Load debtags database
debtags_db = debtags.DB()
tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
try:
    debtags_db.read(open(DB_PATH, "r"), lambda x: not tag_filter.match(x))
except IOError:
    print >> sys.stderr, "IOError: could not open debtags file \'%s\'" % DB_PATH
    exit(1)

# Set of installed packages
installed_pkgs = commands.getoutput('/usr/bin/dpkg --get-selections').replace('install','\t').split()
installed_pkgs_tags = debtags_db.choose_packages(installed_pkgs)

# Most relevant tags
rel_index = debtags.relevance_index_function(debtags_db, installed_pkgs_tags)
relevant_tags = sorted(installed_pkgs_tags.iter_tags(), lambda a, b: cmp(rel_index(a), rel_index(b)))
normalized_relevant_tags = normalize_tags(' '.join(relevant_tags[-50:]))

if not REINDEX:
    try:
        print "Opening existing debtags xapian index at \'%s\'" % INDEX_PATH
        debtags_index = xapian.Database(INDEX_PATH)
    except DatabaseError:
        print "Could not open debtags xapian index"
        REINDEX = 1

if REINDEX:
    debtags_index = createDebtagsIndex(debtags_db,INDEX_PATH)

qp = xapian.QueryParser()
query = qp.parse_query(normalized_relevant_tags)
enquire = xapian.Enquire(debtags_index)
enquire.set_query(query)

mset = enquire.get_mset(0, 20, None, pkgmatchdecider(installed_pkgs))
for m in mset:
    print "%2d: %s" % (m.rank, m.document.get_data())
