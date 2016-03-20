from numpy import array, where

INVALID_PARAMETERS = -1


def sample_classification(percent, labels, threshold):

    if len(labels) != len(threshold):
        return INVALID_PARAMETERS

    for index, value in enumerate(threshold):
        if percent >= value:
            return labels[index]

    return labels[-1]


def create_column_matrix(matrix):
    matrix = array(matrix)
    matrix.shape = (len(matrix), 1)
    return matrix


def create_binary_matrix(original_vector, value, default_value):
    return where(original_vector == value, 1, default_value)
