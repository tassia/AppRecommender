#!/usr/bin/env python

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
        values_plot.append(sum(values) / len(values))

    fig = plt.figure()
    width = .35
    ind = np.arange(len(values_plot))
    plt.bar(ind, values_plot, width=width)
    plt.xticks(ind + width / 2, metrics_plot)
    plt.yticks(np.arange(0.0, 1.1, 0.1))
    plt.grid(axis='y', linestyle='-')

    for a, b in zip(ind, values_plot):
        plt.text(a, b, str(b)[0:5])

    fig.autofmt_xdate()

    plt.show()


def main():
    folder_path = get_folder_path()
    all_folders_path = get_all_folders_path(folder_path)
    files_path = get_cross_validations_path(all_folders_path)
    metrics_values = get_metrics_values(files_path)
    plt_cross_validation_averages(metrics_values)


if __name__ == '__main__':
    main()
