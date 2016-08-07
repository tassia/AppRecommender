import argparse


def get_parser():
    apprec_description = 'Package recommender system for Debian (and derived) \
                          distros'
    parser = argparse.ArgumentParser(description=apprec_description)

    parser.add_argument(
        '-s', '--strategy',
        help='select strategy to run apprecommender (default: cb)',
        type=str)

    parser.add_argument(
        '-d', '--debug',
        help='run apprecommender on debug mode',
        type=int)

    parser.add_argument(
        '-v', '--verbose',
        help='run apprecommender on verbose mode',
        type=int)

    parser.add_argument(
        '-z', '--profile-size',
        help='set the profile size of an user on apprecommender',
        type=int)

    parser.add_argument(
        '-i', '--init',
        help='initialize apprecommender database',
        action='store_true')

    parser.add_argument(
        '-t', '--train',
        help='train machine learning algorithms',
        action='store_true')

    parser.add_argument(
        '-b', '--because',
        help="display which user's packages generated a recommendation",
        action='store_true')

    parser.add_argument(
        '-n', '--num-recommendations',
        help='set the number of packages that will be recommended',
        type=int)

    parser.add_argument(
        '-c', '--contribute',
        help='classify recommendations and help apprecommender to improve',
        action='store_true')

    parser.add_argument(
        '-p', '--packages',
        help="Add reference package for strategy 'cbpkg'",
        type=str, nargs='+', default=[])

    return parser
