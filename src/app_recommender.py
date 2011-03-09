#!/usr/bin/python

#  AppRecommender - A GNU/Linux application recommender
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
from data import *
from evaluation import *
from similarity_measure import *
from recommender import *
from strategy import *
from user import *

# Setup configuration
DB_PATH = "/var/lib/debtags/package-tags"
INDEX_PATH = os.path.expanduser("~/.app-recommender/debtags_index")

XAPIANDBPATH = os.environ.get("AXI_DB_PATH", "/var/lib/apt-xapian-index")
XAPIANDB = XAPIANDBPATH + "/index"
XAPIANDBVALUES = XAPIANDBPATH + "/values"

if __name__ == '__main__':

    reindex = 0
    axi = 0
    if len(sys.argv) == 2:
        if sys.argv[1] == "axi":
            axi = 1
        else:
            DB_PATH = sys.argv[1]
            reindex = 1
    elif len(sys.argv) > 2:
        print >> sys.stderr, ("Usage: %s [PATH_TO_DEBTAGS_DATABASE]" %
                              sys.argv[0])
        sys.exit(1)

    if axi:
        axi_db = xapian.Database(XAPIANDB)
        app_rec = Recommender(axi_db)
        app_rec.set_strategy(AxiContentBasedStrategy())
    else:
        debtags_db = DebtagsDB(DB_PATH)
        if not debtags_db.load():
            print >> sys.stderr,("Could not load DebtagsDB from %s." % DB_PATH)
            sys.exit(1)
        debtags_index = DebtagsIndex(
                             os.path.expanduser("~/.app-recommender/debtags_index"))
        debtags_index.load(debtags_db,reindex)
        app_rec = Recommender(debtags_index)
        app_rec.set_strategy(ContentBasedStrategy())

    user = LocalSystem()
    result = app_rec.get_recommendation(user)
    result.print_result()

    metrics = []
    metrics.append(Precision())
    metrics.append(Recall())
    validation = CrossValidation(0.1,10,app_rec,metrics)
    validation.run(user)
