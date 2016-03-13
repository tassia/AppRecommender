from numpy import array
from src.evaluation import CrossValidation

class CrossValidationMachineLearning(CrossValidation):

    def __init__(self, partition_proportion, rounds, rec,
                 metrics_list, result_proportion, time_pkg_labels_path):
        self.time_pkg_labels_path = time_pkg_labels_path
        super(CrossValidationMachineLearning,
              self).__init__(partition_proportion, rounds, rec, metrics_list,
                             result_proportion)

    def get_model(self, cross_item_score):
        '''
        This function should get the data that will be used as training data,
        train the algorithm with this data and return the generated model
        '''
        # train_bayes_network
        # return bayes_network
        pass

    def get_pkg_score(self, user):
        return user.get_time_score(self.time_pkg_labels_path)

    def get_predicted_results(self, round_user, round_partition, result_size):
        '''
        This method should generate the predictions for the packages
        received. It basically needs to used the generated model
        and use it to generate the prediction.
        '''
        # use the round_partition data on the model representes by round_user
        # return a column_vector that represents the predicted results for
        # round partition
        pass

    def get_real_results(self, round_partition):
        '''
        This method should return the real labels for the validation
        set used on the algorithm.
        '''
        classifications = []
        num_test = len(round_partition)

        for input_vector in round_partition.values():
            classifications.append(input_vector[-1])

        # make classifications a column array
        classifications = array(classifications)
        classifications.shape = (num_test, 1)

        return classifications

    def run_metrics(self, predicted_result, real_result):
        pass
