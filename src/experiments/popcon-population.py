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
import os
import random
import sys

def get_population_profile(popcon):
    profiles_size = []
    for n in range(1,popcon.get_doccount()):
        user = popcon.get_document(n)
        pkgs_profile = [t.term for t in user.termlist() if t.term.startswith("XP")]
        if len(pkgs_profile)<10:
            print "-- profile<10:",user.get_data()
        profiles_size.append(len(pkgs_profile))
    max_profile = max(profiles_size)
    population_profile = [(n,profiles_size.count(n))
                          for n in range(max_profile+1)
                          if profiles_size.count(n)>0 ]
    return population_profile,max_profile

def get_profile_ranges(population_profile,max_profile,popcon_size):
    ranges = range(0,251,50)
    ranges.append(max_profile)
    ranges_population = []
    ranges_percentage = []
    for maximum in ranges[1:]:
        minimum = ranges[ranges.index(maximum)-1]
        valid = [x[1] for x in population_profile
                 if x[0]>minimum and x[0]<=maximum]
        ranges_population.append((maximum,sum(valid)))
        ranges_percentage.append((maximum,sum(valid)/float(popcon_size)))
    return ranges_population,ranges_percentage

def plot(data,xlabel,ylabel,output):
    g = Gnuplot.Gnuplot()
    g('set style data points')
    g.xlabel(xlabel)
    g.ylabel(ylabel)
    g.plot(data)
    g.hardcopy(output+".png", terminal="png")
    g.hardcopy(output+".ps", terminal="postscript", enhanced=1, color=1)

if __name__ == '__main__':
    popcon = xapian.Database(os.path.expanduser("~/.app-recommender/popcon_desktopapps"))
    print ("Popcon repository size: %d" % popcon.get_doccount())

    profile_population,max_profile =  get_population_profile(popcon)
    ranges_population,ranges_percentage = get_profile_ranges(profile_population,
                                                             max_profile,popcon.get_doccount())
    print "Population per profile range (up to index)"
    print ranges_population
    plot(profile_population,"Desktop profile size","Population size",
         "results/misc-popcon/profile_population")
