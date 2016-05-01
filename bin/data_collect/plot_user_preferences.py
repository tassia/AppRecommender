#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np

from load_data import get_csv_file_path, get_lines_from_csv_file

STRATEGIES = ['cbh', 'cbml', 'cbtm']
CLASSIFICATIONS = ['Bad', 'Redundant', 'Useful', 'Useful Surprise']


def autolabel(ax, rects, string_format):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2.,
                1.02 * height, string_format % height,
                ha='center', va='bottom')


def plot_strategies_score(strategies_score, classifications, title, ylabel,
                          plot_min, plot_max, plot_step, string_format='%d'):
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


def load_csv_file(csv_file_path):
    lines = get_lines_from_csv_file(csv_file_path)

    scores = []
    for line in lines[1:]:
        begin = 0
        for strategy in STRATEGIES:
            score = [strategy] + map(int, line[begin: begin + 4])
            begin += 4
            scores.append(score)

    return scores, CLASSIFICATIONS


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

    plot_strategies_score(sum_scores, classifications,
                          'Amount by classification', 'Amount', 0.0, 55.0,
                          5.0)


if __name__ == '__main__':
    main()
