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

DB_PATH = "/var/lib/debtags/package-tags"
INDEX_PATH = os.path.expanduser("~/.app-recommender/debtags_index")

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

    debtags_db = DebtagsDB(DB_PATH)
    if not debtags_db.load(): sys.exit(1)

    user = LocalSystem()
    recommender = Recommender(items_repository=debtags_db,
                              strategy=ContentBasedStrategy(reindex))

    result = recommender.generate_recommendation(user)
    result.print_result()
