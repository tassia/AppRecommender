#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np

from load_data import get_csv_file_path, get_lines_from_csv_file


def plot_cross_validation_averages(metrics_values):
    values_plot = []
    metrics_plot = []
    for metric, values in metrics_values.iteritems():
        metrics_plot.append(metric)
        values_plot.append(values)

    fig = plt.figure()
    width = .35
    ind = np.arange(len(values_plot))
    plt.bar(ind, values_plot, width=width)
    plt.xticks(ind + width / 2, metrics_plot)
    plt.yticks(np.arange(0.0, 1.1, 0.1))

    for a, b in zip(ind, values_plot):
        plt.text(a + 0.17, b + 0.02, str(b)[0:5], ha='center')

    fig.autofmt_xdate()

    plt.show()


def load_csv_file(csv_file_path):
    lines = get_lines_from_csv_file(csv_file_path)

    metrics = [metric for metric in lines[0]]
    values = [map(float, line) for line in lines[1:]]

    return values, metrics


def get_metrics_values(values, metrics):
    metrics_values = dict((metric, 0) for metric in metrics)

    for i in range(len(values)):
        for j in range(len(values[i])):
            metrics_values[metrics[j]] += values[i][j]

    for metric in metrics:
        metrics_values[metric] /= len(values)

    return metrics_values


def main():
    csv_file_path = get_csv_file_path()
    values, metrics = load_csv_file(csv_file_path)
    metrics_values = get_metrics_values(values, metrics)

    plot_cross_validation_averages(metrics_values)


if __name__ == '__main__':
    main()
