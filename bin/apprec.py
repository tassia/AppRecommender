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
import xapian

sys.path.insert(0, '../')

from src.app_recommender import AppRecommender
from src.initialize import Initialize
from src.load_options import LoadOptions


def call_initialize(options):
    for option, _ in options:
        if option in ("-i", "--init"):
            return True

    return False


def run_apprecommender():
    try:
        recommendation_size = 20
        no_auto_pkg_profile = True

        app_recommender = AppRecommender()
        app_recommender.make_recommendation(recommendation_size,
                                            no_auto_pkg_profile)
    except (xapian.DatabaseOpeningError), error:
        print "\n"
        print "Please, Initialize AppRecommender"
        print "Run: apprec.py --init"


def main():

    load_options = LoadOptions()
    load_options.load()

    if call_initialize(load_options.options):
        print "Initializating AppRecommender"
        initialize = Initialize()
        initialize.prepare_data()
    else:
        run_apprecommender()


if __name__ == '__main__':
    main()
