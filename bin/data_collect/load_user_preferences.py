#!/usr/bin/env python

import commands
import matplotlib.pyplot as plt
import numpy as np

from collections import Counter
from load_data import get_folder_path, get_all_folders_path


def load_user_preferences(folder_path):
    preferences_file = "{}user_preferences.txt".format(folder_path)

    user_preferences = {}
    with open(preferences_file, 'rb') as text:
        lines = [line.strip() for line in text]
        user_preferences = dict([(line.split(':')[0], int(line.split(':')[1]))
                                for line in lines])

    return user_preferences


def load_strategies(folder_path):
    all_files = commands.getoutput("ls {}".format(folder_path)).splitlines()
    files = [f for f in all_files if f.endswith('recommendation.txt')]

    strategies = {}
    strategy_names = [f.split('_')[0] for f in files]
    for strategy in strategy_names:
        strategy_file = "{}{}_{}".format(folder_path, strategy,
                                         'recommendation.txt')
        with open(strategy_file, 'rb') as text:
            strategies[strategy] = [line.strip() for line in text]

    return strategies


def get_strategies_score(strategies, user_preferences):
    classifications = {1: 'Bad', 2: 'Redundant', 3: 'Useful',
                       4: 'Useful Surprise'}

    strategies_score = {}
    for strategy, pkgs in strategies.iteritems():
        strategies_score[strategy] = {'Bad': 0, 'Redundant': 0, 'Useful': 0,
                                      'Useful Surprise': 0}

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


def autolabel(ax, rects):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2.,
                1.05 * height, '%d' % int(height),
                ha='center', va='bottom')


def plot_strategies_score(strategies_score):
    colors = {'Bad': 'red', 'Redundant': 'orange', 'Useful': 'yellow',
              'Useful Surprise': 'green'}
    classifications = ['Bad', 'Redundant', 'Useful', 'Useful Surprise']

    groups_number = len(strategies_score)
    std = [3] * groups_number
    ind = np.arange(groups_number)
    width = 0.2

    rects = []
    fig, ax = plt.subplots()
    for index, classification in enumerate(classifications):
        values = []
        for _, score in strategies_score.iteritems():
            values.append(score[classification])
        rects.append(ax.bar(ind + (width * index), values, width,
                     color=colors[classification], yerr=std))

    ax.set_ylabel('Amount')
    ax.set_title('Amount by classification')
    ax.set_xticks(ind + width)
    ax.set_xticklabels(strategies_score.keys())

    ax.legend([r[0] for r in rects], classifications)

    for rect in rects:
        autolabel(ax, rect)

    plt.show()


def get_all_strategies_score(all_folders_path):
    all_strategies_score = []
    for folder_path in all_folders_path:
        strategies = load_strategies(folder_path)
        user_preferences = load_user_preferences(folder_path)
        strategies_score = get_strategies_score(strategies, user_preferences)

        all_strategies_score.append(strategies_score)

    return all_strategies_score


def get_all_strategies(all_strategies_score):
    strategies = set()
    for strategies_score in all_strategies_score:
        strategies |= set(strategies_score.keys())

    return strategies


def get_sum_of_strategies_score(all_strategies_score, strategies):
    sum_strategies_score = {}
    for strategy in strategies:
        strategies_counter = [Counter(strategies_score[strategy])
                              for strategies_score in all_strategies_score]
        sum_strategies_score[strategy] = sum(strategies_counter, Counter())

    return sum_strategies_score


def main():
    folder_path = get_folder_path()
    all_folders_path = get_all_folders_path(folder_path)
    all_strategies_score = get_all_strategies_score(all_folders_path)
    strategies = get_all_strategies(all_strategies_score)
    sum_strategies_score = get_sum_of_strategies_score(all_strategies_score,
                                                       strategies)

    plot_strategies_score(sum_strategies_score)


if __name__ == '__main__':
    main()
