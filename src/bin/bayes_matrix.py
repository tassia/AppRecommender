import pickle
import numpy as np


class BayesMatrix:

    @staticmethod
    def save(bayes_matrix, file_path):
        with open(file_path, 'wb') as text:
            pickle.dump(bayes_matrix, text)

    @staticmethod
    def load(file_path):
        with open(file_path, 'rb') as text:
            bayes_matrix = pickle.load(text)

        return bayes_matrix

    def __init__(self):
        self.D = None
        self.B = None
        self.L = None
        self.A = None
        self.H = None
        self.R = None
        self.PH = None
        self.PR1 = None
        self.DIAG_H = None

    def training(self, attribute_matrix, classifications,
                 order_of_classifications):
        self.D = attribute_matrix.astype(float)
        self.B = (self.convert_order_of_classifications_on_numbers(
                  order_of_classifications).astype(float))
        self.L = (self.convert_classifications_on_numbers(classifications,
                  order_of_classifications,
                  self.B).astype(float))
        self.A = self.get_adjacent_matrix(self.L,
                                          self.B.shape[0],
                                          self.D.shape[0]).astype(float)

        self.H = self.A.dot(np.ones((self.D.shape[0], 1)))
        self.PH = self.H/self.D.shape[0]

        self.R = self.A * self.D

        self.DIAG_H = np.diag(np.array(self.H)[:, 0])
        self.PR1 = np.linalg.inv(self.DIAG_H)*self.R
        self.PR2 = 1 - self.PR1

        self.PR1 = np.eye(self.PR1.shape[1], self.PR1.shape[0]) * self.PR1
        self.PR2 = np.eye(self.PR2.shape[1], self.PR2.shape[0]) * self.PR2

        # v_linha = 1 - V
        # PV1 = PR1 * np.diag(np.array(V.T)[:, 0])
        # PV2 = PR2 * np.diag(np.array(v_linha.T)[:, 0])

        # PV = PV1 + PV2 + 1
        # U = np.log(PV).sum(axis=1)

        # PH = np.log(PH + 1)
        # U = np.eye(B.shape[0], D.shape[1]) * U
        # U = np.diag(np.array(PH)[:, 0]) * U

        # print U

    def convert_order_of_classifications_on_numbers(self,
                                                    order_of_classifications):
        numbers = ""
        for i in range(len(order_of_classifications)):
            numbers += "{0};".format(i)

        return np.matrix(numbers[0:-1])

    def convert_classifications_on_numbers(self, classifications,
                                           order_of_classifications, B):
        numbers = ""
        for i in range(len(classifications)):
            number = order_of_classifications.index(classifications[i])
            numbers += "{0};".format(number)

        return np.matrix(numbers[0:-1])

    def get_adjacent_matrix(self, L, num_labels, num_packages):
        adjacent_matrix = np.zeros((num_labels, num_packages))

        for i in range(len(L)):
            adjacent_matrix[L[i].item()][i] = 1

        return adjacent_matrix
