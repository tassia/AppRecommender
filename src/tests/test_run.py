#!/usr/bin/env python

import os
import unittest
import logging
import bin.apprec as apprec

from src.config import Config


class RunTests(unittest.TestCase):

    def setUp(self):
        logging.getLogger().disabled = True

        self.axi_desktopapps = Config().axi_desktopapps

    def tearDown(self):
        Config().axi_desktopapps = self.axi_desktopapps

    def test_success_run_apprec(self):
        logging.getLogger().disabled = False
        result = apprec.run()

        self.assertEqual(apprec.SUCCESS, result)

    def test_error_init_on_run_apprec(self):
        Config().axi_desktopapps = "asd"
        result = apprec.run()

        self.assertEqual(apprec.ERROR_INIT, result)

    def test_error_init_on_run_apprec(self):
        config = Config()
        strategy = config.strategy
        config.strategy = 'mlbva'

        result = apprec.run()

        config.strategy = strategy

        self.assertEqual(apprec.ERROR_TRAIN, result)
