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

from apprecommender.app_recommender import AppRecommender
from apprecommender.initialize import Initialize
from apprecommender.load_options import LoadOptions
from apprecommender.config import Config
from apprecommender.strategy import (MachineLearning, MachineLearningBVA,
                                     MachineLearningBOW)

SUCCESS = 0
ERROR_INIT = 1
ERROR_TRAIN = 2


def call_initialize(options):
    for option, _ in options:
        if option in ("-i", "--init"):
            return True

    return False


def run_apprecommender(options):
    try:
        recommendation_size = 8

        app_recommender = AppRecommender()
        app_recommender.make_recommendation(recommendation_size)
        return SUCCESS
    except xapian.DatabaseOpeningError:
        return ERROR_INIT
    except IOError:
        if "ml" in Config().strategy:
            return ERROR_TRAIN


def call_training(options):
    for option, _ in options:
        if option in ("-t", "--train"):
            return True

    return False


def run():
    load_options = LoadOptions()
    load_options.load()

    if call_initialize(load_options.options):
        print "Initializing AppRecommender"
        initialize = Initialize()
        initialize.prepare_data()
        return SUCCESS
    elif call_training(load_options.options):
        print "Training machine learning"
        MachineLearning.train(MachineLearningBVA)
        MachineLearning.train(MachineLearningBOW)
        return SUCCESS
    else:
        return run_apprecommender(load_options.options)


def main():
    result = run()

    if result is ERROR_INIT:
        print "\n"
        print "Please, Initialize AppRecommender"
        print "Run: apprec.py --init"
    elif result is ERROR_TRAIN:
        print "\n"
        print "Please, run Machine Learning Training"
        print "Run: apprec.py --train"


if __name__ == '__main__':
    main()
