#!/usr/bin/env python

import os
import commands


class Initialize:

    def __init__(self):
        pass

    def prepare_data(self):
        script_path = os.path.dirname(os.path.abspath(__file__))
        script_path += '/../bin/prepare_data.sh'

        commands.getoutput(script_path)
