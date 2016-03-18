import numpy as np

from src.evaluation import CrossValidation
from data import MachineLearningData
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

    def run(self):
        matrix_values = np.zeros(shape=(2, 2))
        num_classification = len(self.predicted_results)

        for i in range(num_classification):
            row = self.predicted_results[i][0]
            column = self.real_results[i][0]

            matrix_values[row][column] += 1

        self.true_positive_len = matrix_values[0][0]
        self.true_negative_len = matrix_values[1][1]
        self.false_positive_len = matrix_values[0][1]
        self.false_negative_len = matrix_values[1][0]


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

    def __init__(self, partition_proportion, rounds,
                 metrics_list, labels, thresholds):

        self.ml_data = MachineLearningData()
        self.labels = labels
        self.thresholds = thresholds

        super(CrossValidationMachineLearning,
              self).__init__(partition_proportion, rounds, None,
                             metrics_list, 0)

    def __str__(self):
        result_str = ''
        for metric in self.metrics_list:
            result_str += '{0}:\n'.format(metric.desc)

            for r in range(self.rounds):
                result_str += '\tRound {0}:\n'.format(r)

                mean = 0
                for label in self.labels:
                    result = self.cross_results[metric.desc][r][label]
                    mean += result
                    result_str += '\t\tClass {0}: {1}\n'.format(label, result)

                result_str += '\t\tMean: {0}\n\n'.format(mean / len(self.labels))

        return result_str


    def get_model(self, cross_item_score):
        '''
        This function should get the data that will be used as training data,
        train the algorithm with this data and return the generated model
        '''
        bayes_matrix = BayesMatrix()

        all_matrix = (np.matrix(cross_item_score.values()))
        data_matrix = all_matrix[0:, 0:-1]
        classifications = all_matrix[0:, -1]

        bayes_matrix.training(data_matrix, classifications,
                              self.labels)

        return bayes_matrix

    def get_user_score(self, user):
        return self.ml_data.create_data(self.labels, self.thresholds)

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
