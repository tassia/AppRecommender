#!/usr/bin/env python

from src.strategy import MachineLearningBVA, MachineLearningBOW


class MachineLearningTraing:

    def __init__(self):
        self.ml_strategies = []
        self.ml_strategies.append(MachineLearningBVA('machine-learning', 10))
        self.ml_strategies.append(MachineLearningBOW('machine-learning', 10))

    def train(self):
        for ml_strategy in self.ml_strategies:
            ml_strategy.train()
