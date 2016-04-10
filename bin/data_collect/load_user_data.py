#!/usr/bin/env python

import os
import commands


def load_user_preferences(folder_path):
    preferences_file = "{}user_preferences.txt".format(folder_path)

    user_preferences = {}
    with open(preferences_file, 'rb') as text:
        lines = [line.strip() for line in text]
        user_preferences = dict([(element.split(':')[0], int(element.split(':')[1])) for element in lines])

    return user_preferences


def load_strategies(folder_path):
    all_files = commands.getoutput("ls {}".format(folder_path)).splitlines()
    files = [f for f in all_files if f.endswith('recommendation.txt')]

    strategies = {}
    strategy_names = [f.split('_')[0] for f in files]
    for strategy in strategy_names:
        strategy_file = "{}{}_{}".format(folder_path, strategy, 'recommendation.txt')
        with open(strategy_file, 'rb') as text:
            strategies[strategy] = [line.strip() for line in text]

    return strategies


def get_strategies_score(strategies, user_preferences):
    classifications = {1: 'Bad', 2: 'Redundant', 3: 'Useful', 4: 'Useful Surprise'}

    strategies_score = {}
    for strategy, pkgs in strategies.iteritems():
        strategies_score[strategy] = {'Bad': 0, 'Redundant': 0, 'Useful': 0, 'Useful Surprise': 0}

        for pkg in pkgs:
            classification = classifications[user_preferences[pkg]]
            strategies_score[strategy][classification] += 1

    return strategies_score


def print_strategies_score(strategies_score):
    classifications = ['Bad', 'Redundant', 'Useful', 'Useful Surprise']

    for strategy, score in strategies_score.iteritems():
        print "\nStrategy: {}".format(strategy)

        for classification in classifications:
            print "  {}: {}".format(classification, score[classification])
    print '\n'


def main(folder_path):
    strategies = load_strategies(folder_path)
    user_preferences = load_user_preferences(folder_path)
    strategies_score = get_strategies_score(strategies, user_preferences)

    print_strategies_score(strategies_score)


if __name__ == '__main__':
    folder_path = '~/app_recommender_log201604081638/'
    folder_path = os.path.expanduser(folder_path)
    main(folder_path)
