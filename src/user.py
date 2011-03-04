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

class User:
    """  """
    def __init__(self,item_score,user_id=0,demo_profile=0):
        """  """
        self.id = user_id
        self.item_score = item_score
        self.demo_profile = demo_profile

    def items(self):
        return self.item_score.keys()

class LocalSystem(User):
    """  """
    def __init__(self):
        item_score = {}
        dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')
        for p in dpkg_output.replace('install','\t').split():
            item_score[p] = 1
        User.__init__(self,item_score)
