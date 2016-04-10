#!/usr/bin/env python

import os
import commands


def load_recommendations(folder_path):
    all_files = commands.getoutput("ls {}".format(folder_path)).splitlines()
    files = [f for f in all_files if f.endswith('recommendation.txt')]
    preferences_file = "{}user_preferences.txt".format(folder_path)

    with open(preferences_file, 'rb') as text:
        lines = [line.strip() for line in text]
        print lines

    strategies = [f.split('_')[0] for f in files]
    for strategy in strategies:
        strategy_file = "{}{}_{}".format(folder_path, strategy, 'recommendation.txt')
        print strategy_file


if __name__ == '__main__':
    folder_path = 'app_recommender_log201604081638/'
    folder_path = os.path.join(os.path.expanduser('~'), folder_path)
    load_recommendations(folder_path)
