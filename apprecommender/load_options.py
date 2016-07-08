#!/usr/bin/env python

import getopt
import sys
import logging

from apprecommender.config import Config
from apprecommender.singleton import Singleton


class LoadOptions(Singleton):

    def __init__(self):
        self.options = []

    def load(self):
        config = Config()
        short_options = 'hdvo:d:v:s:z:idvo:tdvo:b:n:cdvo'
        long_options = ['help', 'debug', 'verbose', 'strategy=',
                        'profile_size=', 'init', 'train', 'because',
                        'nrecommendation', 'contribute']
        try:
            opts, args = getopt.getopt(sys.argv[1:], short_options,
                                       long_options)
            self.options = opts
        except getopt.GetoptError as error:
            config.set_logger()
            logging.error('Bad syntax: {}'.format(str(error)))
            self.usage()
            sys.exit()

        for o, p in opts:
            if o in ('-h', '--help'):
                self.usage()
                sys.exit()
            elif o in ('-d', '--debug'):
                config.debug = 1
            elif o in ('-v', '--verbose'):
                config.verbose = 1
            elif o in ('-s', '--strategy'):
                config.strategy = p
            elif o in ('-z', '--profile_size'):
                config.profile_size = int(p)
            elif o in ('-i', '--init'):
                continue
            elif o in ('-t', '--train'):
                continue
            elif o in ('-b', '--because'):
                config.because = True
            elif o in ('-n', '--num-recommendations'):
                config.num_recommendations = int(p)
            elif o in ('-c', '--contribute'):
                continue
            else:
                assert False, "unhandled option"

        config.set_logger()

    def usage(self):
        """
        Print usage help.
        """
        print "[FIXME: deprecated help]"
        print "\n [ general ]"
        print "  -h, --help                 Print this help"
        print "  -i, --init                 Initialize AppRecommender data"
        print "  -t, --train                Make training of AppRecommender" \
              " machine learning"
        print "  -n, --num-recommendations  Set the number of packages that" \
              " will be recommended"
        print "  -b, --because              Display user packages that" \
              " generated a given recommendation"
        print "  -d, --debug                Set logging level to debug"
        print "  -v, --verbose              Set logging level to verbose"
        print ""
        print " [ recommender ]"
        print "  -s, --strategy=OPTION      Recommendation strategy"
        print "  -z, --profilesize=k        Size of user profile"
        print ""
        print " [ strategy options ] "
        print "  cb = content-based, mixed profile"
        print "  cbt = content-based, tags only profile"
        print "  cbd = content-based, description terms only profile"
        print "  cbh = content-based, half-half profile"
        print "  cbtm = content-based, time-context profile"
        print "  cb_eset = cb with eset profiling"
        print "  cbt_eset = cbt with eset profiling"
        print "  cbd_eset = cbd_eset with eset profiling"
        print "  cbh_eset = cbh with eset profiling"
        print "  mlbva = machine_learning, Binary Vector Approach"
        print "  mlbow = machine_learning, Bag Of Words"
        print ""
        print " [ contribute with AppRecommender ]"
        print "  -c, --contribute           classify recommendations" \
              " helping AppRecommender to improve recommendations"
