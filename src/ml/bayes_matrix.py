import pickle
import numpy as np


class BayesMatrix:
    '''
    This class contains the implementation of the naive bayes algorithm using
    only matrix operations in order to perform its tasks.
    '''

    @staticmethod
    def save(bayes_matrix, file_path):
        with open(file_path, 'wb') as text:
            pickle.dump(bayes_matrix, text)

    @staticmethod
    def load(file_path):
        with open(file_path, 'rb') as text:
            bayes_matrix = pickle.load(text)

        return bayes_matrix

    '''
    data:                 A matrix on the format p x a, where p is the number
                          of packages that will be used to train the
                          algorithm and a is the number of features that a
                          package has.

    classifications:      A matrix that holds the temporal classification
                          labels for the packages found on the
                          attributes' matrix. This matrix is a column one,
                          where the number of lines represents the number of
                          packages used to train the algorithm.

    order_of_classifications:   A array with the possible classifications
                                on crescent order

    labels:               A column matrix that holds the possible labels that
                          can be used to classify a given package.

    adjacency:            A matrix in the format l x p, where l is the number
                          of possible classifications labels. This is a binary
                          matrix that holds which packages were classified
                          with some given label.

    histogram:            A column vector l x 1, where l is the possible
                          classification labels. This matrix holds the values
                          of how many packages p were classified with a
                          given label l.

    label_probability:    A column matrix that holds the individual
                          probability for each label l for the given
                          training data.

    feature_per_label:    A l x a matrix that hold for each label, the number
                          of times a feature a was present on the label.

    prob:               A l x a matrix that holds the probability of a given
                          feature a to be present in a given label l.

    diag_histogram:       A diagonal matrix for the histogram one.

    attribute_vector:     A vector 1 x a with the values of features to get a
                          classification for this vector based on the
                          training

    '''
    def __init__(self):
        self.data = None
        self.classifications = None
        self.labels = None
        self.adjacecy = None
        self.histogram = None
        self.label_probability = None
        self.feature_per_label = None
        self.prob = None
        self.diag_histogram = None

    def training(self, data_matrix, classifications,
                 order_of_classifications):
        self.data = data_matrix.astype(float)
        order_of_classifications = order_of_classifications[:]
        self.used_order_of_classifications = (
            self.get_used_order_of_classifications(classifications,
                                                   order_of_classifications))
        self.labels = (self.convert_possible_labels_to_number(
            self.used_order_of_classifications).astype(float))

        num_packages = self.data.shape[0]
        num_labels = self.labels.shape[0]

        self.classifications = (self.convert_classifications_to_number(
            classifications, self.used_order_of_classifications).astype(float))

        self.adjacency = self.get_adjacent_matrix(num_labels,
                                                  num_packages).astype(float)

        self.histogram = self.adjacency.dot(np.ones((num_packages, 1)))
        self.label_probability = self.histogram / num_packages

        self.feature_per_label = self.adjacency * self.data

        self.diag_histogram = np.diag(np.array(self.histogram)[:, 0])
        self.prob = np.linalg.inv(
            self.diag_histogram) * self.feature_per_label

    def get_classification(self, attribute_vector):
        attribute_vector = attribute_vector.astype(float)
        prob_vector = self.prob.copy()
        label_probability_log = np.log(self.label_probability + 1)

        indexes_one = np.matrix(np.where(attribute_vector == 1.0)[1])
        indexes_one = indexes_one.tolist()[0]
        indexes_zero = np.matrix(np.where(attribute_vector == 0.0)[1])
        indexes_zero = indexes_zero.tolist()[0]

        prob_vector[:, indexes_one] = 1 + prob_vector[:, indexes_one]
        prob_vector[:, indexes_zero] = 2 - prob_vector[:, indexes_zero]

        prob_vector = np.log(prob_vector)
        prob_vector = prob_vector * np.ones((prob_vector.shape[1], 1))
        prob_vector = label_probability_log + prob_vector

        line, col = np.unravel_index(prob_vector.argmax(), prob_vector.shape)
        best_prob_index = line

        return self.used_order_of_classifications[best_prob_index]

    def convert_possible_labels_to_number(self, order_of_classifications):
        numbers = ""
        for i in range(len(order_of_classifications)):
            numbers += "{0};".format(i)

        return np.matrix(numbers[0:-1])

    def convert_classifications_to_number(self, classifications,
                                          order_of_classifications):
        numbers = ""
        for i in range(len(classifications)):
            number = order_of_classifications.index(classifications[i])
            numbers += "{0};".format(number)

        return np.matrix(numbers[0:-1])

    def get_adjacent_matrix(self, num_labels, num_packages):
        adjacent_matrix = np.zeros((num_labels, num_packages))

        for i in range(len(self.classifications)):
            index = int(self.classifications[i].item())
            adjacent_matrix[index][i] = 1

        return adjacent_matrix

    def get_used_order_of_classifications(self, classifications,
                                          order_of_classifications):
        used_classifications = set()
        num_possible_classifications = len(order_of_classifications)

        for name in classifications:
            if len(used_classifications) == num_possible_classifications:
                return order_of_classifications

            used_classifications.add(name[0].item())

        for name in order_of_classifications[:]:
            if name not in used_classifications:
                index = order_of_classifications.index(name)
                del order_of_classifications[index]

        return order_of_classifications
