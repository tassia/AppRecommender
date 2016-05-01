#!/usr/bin/env python

import commands

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


def load_pc_informations(folder_path):
    all_files = commands.getoutput("ls {}".format(folder_path)).splitlines()
    files = [f for f in all_files if f.endswith('informations.txt')]

    informations = {}
    pc_informations_file = '{}{}'.format(folder_path, files[0])
    valid_info = set(['distributor_id', 'codename'])

    with open(pc_informations_file, 'rb') as text:
        for line in text:
            if ':' not in line:
                continue

            info = line.split(':')
            info[0] = info[0].lower().replace(' ', '_')

            if info[0] in valid_info:
                informations[info[0]] = info[1].strip()

    return informations


def get_strategies_score(strategies, user_preferences):
    classifications = {1: 'bad', 2: 'redundant', 3: 'useful',
                       4: 'useful_surprise'}

    strategies_score = {}
    for strategy, pkgs in strategies.iteritems():
        strategies_score[strategy] = {'bad': 0, 'redundant': 0, 'useful': 0,
                                      'useful_surprise': 0}

        for pkg in pkgs:
            classification = classifications[user_preferences[pkg]]
            strategies_score[strategy][classification] += 1

    return strategies_score


def print_strategies_score(strategies_score):
    classifications = ['bad', 'redundant', 'useful', 'useful_surprise']

    for strategy, score in strategies_score.iteritems():
        print "\nStrategy: {}".format(strategy)

        for classification in classifications:
            print "  {}: {}".format(classification, score[classification])
    print '\n'


def get_all_strategies_score(all_folders_path):
    all_strategies_score = []
    for folder_path in all_folders_path:
        strategies = load_strategies(folder_path)
        user_preferences = load_user_preferences(folder_path)
        strategies_score = get_strategies_score(strategies, user_preferences)

        all_strategies_score.append(strategies_score)

    return all_strategies_score


def get_all_pc_informations(all_folders_path):
    all_pc_informations = []

    for folder_path in all_folders_path:
        pc_information = load_pc_informations(folder_path)
        all_pc_informations.append(pc_information)

    return all_pc_informations


def convert_to_csv(all_strategies_score, all_pc_informations):
    rows = []
    possible_strategies = sorted(all_strategies_score[0].keys())
    pc_info_header = sorted(all_pc_informations[0].keys())
    classifications = ['bad', 'redundant', 'useful', 'useful_surprise']

    csv_header = ""

    for strategy in possible_strategies:
        for classification in classifications:
            csv_header += '{}_{};'.format(strategy, classification)

    for info in pc_info_header:
        csv_header += '{};'.format(info)

    rows.append(csv_header[:-1])

    for strategies_score in all_strategies_score:
        row = []

        for strategy, scores in sorted(strategies_score.items()):
            for classification in classifications:
                row.append(scores[classification])

        row = ';'.join(str(element) for element in row)
        rows.append(row)

    index = 1
    for pc_informations, row in zip(all_pc_informations, rows[1:]):
        distributor_id = pc_informations['distributor_id']
        codename = pc_informations['codename']
        row = row + ';{};{}'.format(codename, distributor_id)

        rows[index] = row
        index += 1

    return rows


def main():
    folder_path = get_folder_path()
    all_folders_path = get_all_folders_path(folder_path)
    all_strategies_score = get_all_strategies_score(all_folders_path)
    all_pc_informations = get_all_pc_informations(all_folders_path)

    csv_rows = convert_to_csv(all_strategies_score, all_pc_informations)
    for row in csv_rows:
        print row


if __name__ == '__main__':
    main()
