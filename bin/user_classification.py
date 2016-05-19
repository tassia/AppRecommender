#!/usr/bin/python

import os
import pickle
import sys

sys.path.insert(0, "{0}/../".format(os.path.dirname(__file__)))


def main():
    path = os.path.expanduser(
        '~/.app-recommender/user_data/pkgs_classifications.txt')

    if not os.path.exists(path):
        print 'Could not find file pkgs_classification'
        print 'Have you run apprec --train ?'
        exit(-1)

    with open(path, 'ra') as data:
        pkg_classification = pickle.load(data)

    classifications = {'RU': [], 'U': [], 'NU': []}
    for pkg, values in pkg_classification.iteritems():
        classifications[values[-1]].append(pkg)

    for classification, pkgs in classifications.iteritems():
        print 'Classification: {}'.format(classification)

        for pkg in sorted(pkgs):
            print pkg

        print '\n'

    print 'Num pkgs: {}'.format(len(pkg_classification))


if __name__ == '__main__':
    main()
