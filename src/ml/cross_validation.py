import numpy as np
from collections import defaultdict

from src.evaluation import CrossValidation
from bayes_matrix import BayesMatrix
from utils import create_column_matrix, create_binary_matrix

NOT_NECESSARY = 1


class ConfusionMatrix():

    def __init__(self, predicted_results, real_results):
        self.predicted_results = predicted_results
        self.real_results = real_results
        self.repository_size = len(predicted_results)

        self.true_positive_len = 0
        self.true_negative_len = 0
        self.false_positive_len = 0
        self.false_negative_len = 0

        self.predicted_relevant_len = 0
        self.real_relevant_len = 0
        self.real_negative_len = 0

    def run(self):
        matrix_values = np.zeros(shape=(2, 2))
        num_classification = len(self.predicted_results)

        for i in range(num_classification):
            row = self.predicted_results[i][0]
            column = self.real_results[i][0]

            matrix_values[row][column] += 1

        self.true_positive_len = matrix_values[1][1]
        self.true_negative_len = matrix_values[0][0]
        self.false_positive_len = matrix_values[1][0]
        self.false_negative_len = matrix_values[0][1]

        self.predicted_relevant_len = (self.true_positive_len +
                                       self.false_positive_len)
        self.real_relevant_len = (self.true_positive_len +
                                  self.false_negative_len)

        self.real_negative_len = self.repository_size - self.real_relevant_len

    def __str__(self):

        result = 'TP: {0}\nFP: {1}'.format(self.true_positive_len,
                                           self.false_positive_len)
        result += '\nFN: {0}\nTN: {1}\n'.format(self.false_negative_len,
                                                self.true_negative_len)

        return result


class Evaluation():

    '''
    :param predicted_results: The classifications generated by the machine
                              learning algorithm. This variable will be a
                              column matrix, where the number of lines
                              is equal to the number of data used to
                              validate the algorithm.

    :param real_results:      The real classifications of the data used to
                              test the machine learning algorithm. This
                              variable will be a column matrix, where the
                              number of lines  is equal to the number of
                              data used to validate the algorithm.

    :possible_classification: An list containg the labels that a input vector
                              can be classified upon.
    '''

    def __init__(self, predicted_results, real_results,
                 possible_classifications):
        self.predicted_results = predicted_results
        self.real_results = real_results
        self.possible_classifications = possible_classifications
        self.repository_size = predicted_results.shape[0]

        self.classes_outputs = {}
        self.create_classification_outputs()

    def create_classification_outputs(self):
        for classification in self.possible_classifications:
            self.classes_outputs[classification] = (
                self.create_confusion_matrix(classification))

    def create_confusion_matrix(self, classification):
        default_value = 0

        # Create binary classifications using the one received as parameter
        binary_predictions = create_binary_matrix(self.predicted_results,
                                                  classification,
                                                  default_value)
        binary_real = create_binary_matrix(self.real_results, classification,
                                           default_value)

        confusion_matrix = ConfusionMatrix(binary_predictions, binary_real)
        confusion_matrix.run()
        return confusion_matrix

    def run(self, metric):
        results = {}

        for label, confusion_matrix in self.classes_outputs.iteritems():
            results[label] = metric.run(confusion_matrix)

        return results


class CrossValidationMachineLearning(CrossValidation):

    def __init__(self, pkg_data, partition_proportion, rounds,
                 metrics_list, labels, thresholds):

        self.pkg_data = pkg_data
        self.labels = labels
        self.thresholds = thresholds
        self.label_groups = {}
        self.round_label_groups = []
        self.round_num_data = []

        super(CrossValidationMachineLearning,
              self).__init__(partition_proportion, rounds, None,
                             metrics_list, 0)

    def __str__(self):
        result_str = ''
        metrics_mean = {}
        num_data = len(self.pkg_data)

        result_str += 'Num data used: {0}\n'.format(num_data)

        for label in self.labels:
            result_str += 'Num of data marked as {0}: {1}\n'.format(
                label, len(self.label_groups[label]))

        result_str += '\n\n'

        for r in range(self.rounds):
            result_str += 'Round {0}:\n\n'.format(r)

            result_str += 'Training data used: {0}\n'.format(
                self.round_num_data[r])

            for label in self.labels:
                result_str += 'Data marked as {0}: {1}\n'.format(
                    label, len(self.round_label_groups[r][label]))

            result_str += '\n'

        result_str += '\n\n'

        for metric in self.metrics_list:
            result_str += '{0}:\n'.format(metric.desc)
            metrics_mean[metric.desc] = 0

            for r in range(self.rounds):
                result_str += '\tRound {0}:\n'.format(r)

                mean = 0
                for label in self.labels:
                    result = self.cross_results[metric.desc][r][label]
                    mean += result
                    result_str += '\t\tClass {0}: {1}\n'.format(label, result)

                mean /= len(self.labels)
                result_str += '\t\tMean: {0}\n\n'.format(mean)
                metrics_mean[metric.desc] += mean

            metrics_mean[metric.desc] /= self.rounds

        result_str += '\n\n'
        result_str += 'Average results:\n'
        result_str += '---------------\n'

        for metric in self.metrics_list:
            result_str += '{0}: {1}\n'.format(metric.desc,
                                              metrics_mean[metric.desc])

        return result_str

    def create_labels_groups(self, data):
        label_groups = {}
        label_groups.fromkeys(self.labels)
        label_groups = defaultdict(lambda: [], label_groups)

        for input_vector in data.values():
            label = input_vector[-1]
            label_groups[label].append(input_vector)

        return label_groups

    def get_model(self, cross_item_score):
        '''
        This function should get the data that will be used as training data,
        train the algorithm with this data and return the generated model
        '''

        self.round_num_data.append(len(cross_item_score))
        self.round_label_groups.append(
            self.create_labels_groups(cross_item_score))

        bayes_matrix = BayesMatrix()

        all_matrix = (np.matrix(cross_item_score.values()))
        data_matrix = all_matrix[0:, 0:-1]
        classifications = all_matrix[0:, -1]

        bayes_matrix.training(data_matrix, classifications,
                              self.labels)

        return bayes_matrix

    def get_user_score(self, user):
        user_score = self.pkg_data

        self.label_groups = self.create_labels_groups(user_score)

        return user_score

    '''
    :param round_user: The model created by the machine learning algorithm.

    :param round_partition: The data that will be used to evaluate the
                            machine learning algorithm.

    :param result_size:     Not necessary for this context
    '''
    def get_predicted_results(self, round_user, round_partition,
                              result_size=0):
        '''
        This method should generate the predictions for the packages
        received. It basically needs to used the generated model
        and use it to generate the prediction.
        '''

        predicted_results = []

        for pkg, input_vector in round_partition.iteritems():
            input_vector = np.matrix(input_vector[:-1])
            predicted_results.append(
                round_user.get_classification(input_vector))

        return create_column_matrix(predicted_results)

    def get_real_results(self, round_partition):
        '''
        This method should return the real labels for the validation
        set used on the algorithm.
        '''
        classifications = []

        for input_vector in round_partition.values():
            classifications.append(input_vector[-1])

        # make classifications a column array
        return create_column_matrix(classifications)

    def get_result_size(self):
        return NOT_NECESSARY

    def get_evaluation(self, predicted_result, real_result):
        return Evaluation(predicted_result, real_result, self.labels)
