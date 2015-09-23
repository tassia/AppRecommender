import os
import sys
import unittest


def additional_tests():
    setup_file = sys.modules['__main__'].__file__
    setup_dir = os.path.abspath(os.path.dirname(setup_file))
    setup_dir += '/src/'
    return unittest.defaultTestLoader.discover(setup_dir)
