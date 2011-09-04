#! /usr/bin/env python
"""
    misc_popcon - misc experiments with popcon data
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

import Gnuplot
import xapian

def profile_population():
    popcon = xapian.Database("/home/tassia/.app-recommender/popcon_desktopapps")
    popcon_size = popcon.get_doccount()
    print "User repository size: %d" % popcon_size
    profiles_size = []
    for n in range(1,popcon_size):
        user = popcon.get_document(n)
        profile = [t.term for t in user.termlist()]
        profiles_size.append(len(profile))
    profile_population = [(n,profiles_size.count(n))
                          for n in range(max(profiles_size)+1)
                          if profiles_size.count(n)>0 ]
    ranges_population = []
    ranges_percentage = []
    ranges = range(0,601,50)
    for maximum in ranges[1:]:
        minimum = ranges[ranges.index(maximum)-1]
        valid = [x[1] for x in profile_population
                 if x[0]>minimum and x[0]<=maximum]
        ranges_population.append((maximum,sum(valid)))
        ranges_percentage.append((maximum,sum(valid)/float(popcon_size)))

    g = Gnuplot.Gnuplot()
    g('set style data points') # give gnuplot an arbitrary command
    g.xlabel('Desktop profile size')
    g.ylabel('Population size')
    g.plot(profile_population)
    g.hardcopy('profile_population.png', terminal="png")
    g.hardcopy('profile_population.ps', terminal="postscript", enhanced=1, color=1)
    g.reset()
    g.xlabel('Range Desktop profile size')
    g.ylabel('Population size')
    g.plot(ranges_population)
    g.hardcopy('ranges_profile_population.png', terminal="png")
    g.hardcopy('ranges_profile_population.ps', terminal="postscript", enhanced=1, color=1)
    g.reset()
    g.xlabel('Range Desktop profile size')
    g.ylabel('Population percentage')
    g.plot(ranges_percentage)
    g.hardcopy('ranges_profile_percentage.png', terminal="png")
    g.hardcopy('ranges_profile_percentage.ps', terminal="postscript", enhanced=1, color=1)
if __name__ == '__main__':
    profile_population()

