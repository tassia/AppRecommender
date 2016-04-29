#!/usr/bin/env python

import commands
import matplotlib.pyplot as plt
import numpy as np

from collections import Counter
from load_data import get_folder_path, get_all_folders_path

import os
import sys


def autolabel(ax, rects, string_format):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2.,
                1.02 * height, string_format % height,
                ha='center', va='bottom')


def plot_strategies_score(strategies_score, classifications, title, ylabel, plot_min, plot_max, plot_step, string_format='%d'):
    colors = ['red', 'orange', 'yellow', 'green']

    groups_number = len(strategies_score)
    ind = np.arange(groups_number)
    width = 0.2

    rects = []
    fig, ax = plt.subplots()
    for index, classification in enumerate(classifications):
        values = []
        for _, score in strategies_score.iteritems():
            values.append(score[index])
        rects.append(ax.bar(ind + (width * index), values, width,
                     color=colors[index]))

    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(ind + width)
    ax.set_xticklabels(strategies_score.keys())

    ax.legend([r[0] for r in rects], classifications)

    for rect in rects:
        autolabel(ax, rect, string_format)

    plt.yticks(np.arange(plot_min, plot_max, plot_step))
    plt.show()


def get_csv_file_path():
    usage_message = "Usage: {} [csv_file_path]".format(sys.argv[0])

    if len(sys.argv) < 2:
        print usage_message
        exit(1)

    csv_file_path = sys.argv[1]
    csv_file_path = os.path.expanduser(csv_file_path)

    if not os.path.exists(csv_file_path):
        print usage_message
        print "CSV file not exists"
        exit(1)

    return csv_file_path


def load_csv_file(csv_file_path):
    with open(csv_file_path, 'rb') as text:
        lines = [line.strip() for line in text]

    lines = [line.split(';') for line in lines]

    scores = [[line[0]] + map(int, line[1:]) for line in lines[1:]]
    classifications = lines[0][1:]

    return scores, classifications


def get_sum_of_scores(scores):
    sum_scores = {}

    for score in scores:
        classification = score[0]
        if classification not in sum_scores.keys():
            sum_scores[classification] = [0] * (len(score) - 1)

        for index, value in enumerate(score[1:]):
            sum_scores[classification][index] += value

    return sum_scores


def main():
    csv_file_path = get_csv_file_path()
    scores, classifications = load_csv_file(csv_file_path)
    sum_scores = get_sum_of_scores(scores)


    plot_strategies_score(sum_scores, classifications, 'Amount by classification', 'Amount', 0.0, 55.0, 5.0)


if __name__ == '__main__':
    main()
