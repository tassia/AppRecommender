#!/usr/bin/env python

import os
import sys
import commands
import matplotlib.pyplot as plt
import numpy as np

from load_data import get_folder_path, get_all_folders_path


def get_cross_validations_path(folders_path):
    files = []
    for folder_path in folders_path:
        all_files = commands.getoutput(
            "ls {}".format(folder_path)).splitlines()
        files += [folder_path + f for f in all_files
                  if f.startswith('cross_validation_result')]

    return files


def get_metrics_values(files_path):
    metrics_values = {'S_Accuracy': [], 'Precision': [], 'Recall': [],
                      'FPR': [], 'F(1.0)': []}

    for file_path in files_path:
        with open(file_path, 'rb') as text:
            lines = [line.strip() for line in text]
            for line in lines:
                line_split = line.split(':')
                metric = line_split[0].strip()

                if metric in metrics_values.keys() and len(line_split[1]) > 0:
                    value = float(line_split[1])
                    metrics_values[metric].append(value)

    return metrics_values


def plt_cross_validation_averages(metrics_values):
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

    metrics = [metric for metric in lines[0]]
    values = [map(float, line) for line in lines[1:]]
    metrics_values = dict((metric, 0) for metric in metrics)

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

    plt_cross_validation_averages(metrics_values)


if __name__ == '__main__':
    main()
