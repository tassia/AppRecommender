#!/usr/bin/env python

import sys


def print_progress_bar(number, n_numbers, message='Progress',
                       bar_length=40):
    percent = float(number) / float(n_numbers)
    hashes = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(hashes))
    percent = int(round(percent * 100))

    percent_message = ("\r{}: [{}] [{} / {}] {}%".format(message,
                                                         hashes + spaces,
                                                         number,
                                                         n_numbers,
                                                         percent))
    sys.stdout.write(percent_message)
    sys.stdout.flush()
    if number == n_numbers:
        print '\n'


def get_class_and_module_name(cls):
    class_name = cls.__name__
    module_name = cls.__module__

    return module_name + '.' + class_name
