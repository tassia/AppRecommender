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

import commands
import xapian
import logging

class FilterTag(xapian.ExpandDecider):
    def __call__(self, term):
        """
        Return true if the term is a tag, else false.
        """
        return term[:2] == "XT"

class User:
    """  """
    def __init__(self,item_score,user_id=0,demo_profile=0):
        """  """
        self.id = user_id
        self.item_score = item_score
        self.demo_profile = demo_profile

    def items(self):
        return self.item_score.keys()

    def axi_tag_profile(self,xapian_db,profile_size):
        terms = []
        for item in self.items():
            terms.append("XP"+item)
        query = xapian.Query(xapian.Query.OP_OR, terms)
        enquire = xapian.Enquire(xapian_db)
        enquire.set_query(query)
        rset = xapian.RSet()
        for m in enquire.get_mset(0,30000): #consider all matches
             rset.add_document(m.docid)
        eset = enquire.get_eset(profile_size, rset, FilterTag())
        profile = []
        for res in eset:
            profile.append(res.term)
            logging.debug("%.2f %s" % (res.weight,res.term[2:]))
        return profile

    def debtags_tag_profile(self,debtags_db,profile_size):
        return debtags_db.get_relevant_tags(self.items(),profile_size)

class LocalSystem(User):
    """  """
    def __init__(self):
        item_score = {}
        dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')
        for p in dpkg_output.replace('install','\t').split():
            item_score[p] = 1
        User.__init__(self,item_score)
