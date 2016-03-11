from config import Config

import pickle
import numpy as np

USER_DATA_DIR = Config().user_data_dir


def convert_order_of_classifications_on_numbers(order_of_classifications):
    numbers = ""
    for i in range(len(order_of_classifications)):
        numbers += "{0};".format(i)

    return np.matrix(numbers[0:-1])


def convert_classifications_on_numbers(classifications, order_of_classifications, B):
    numbers = ""
    for i in range(len(classifications)):
        number = order_of_classifications.index(classifications[i])
        numbers += "{0};".format(number)

    return np.matrix(numbers[0:-1])


def training(attribute_matrix, classifications, order_of_classifications):
    D = attribute_matrix.astype(float)
    B = convert_order_of_classifications_on_numbers(order_of_classifications).astype(float)
    L = convert_classifications_on_numbers(classifications, order_of_classifications, B).astype(float)
    A = get_adjacent_matrix(L, B.shape[0], D.shape[0]).astype(float)

    H = A.dot(np.ones((D.shape[0], 1)))
    PH = H/D.shape[0]

    R = A * D

    DIAG_H = np.diag(np.array(H)[:, 0])
    PR1 = np.linalg.inv(DIAG_H)*R
    PR2 = 1 - PR1

    PR1 = np.eye(PR1.shape[1], PR1.shape[0]) * PR1
    PR2 = np.eye(PR2.shape[1], PR2.shape[0]) * PR2

    results = {'PH': PH, 'PR1': PR1, 'PR2': PR2}

    print "Save"
    with open(USER_DATA_DIR + 'machine_learning_training.txt', 'wb') as text:
        pickle.dump(results, text)

    # v_linha = 1 - V
    # PV1 = PR1 * np.diag(np.array(V.T)[:, 0])
    # PV2 = PR2 * np.diag(np.array(v_linha.T)[:, 0])

    # PV = PV1 + PV2 + 1
    # U = np.log(PV).sum(axis=1)

    # PH = np.log(PH + 1)
    # U = np.eye(B.shape[0], D.shape[1]) * U
    # U = np.diag(np.array(PH)[:, 0]) * U

    # print U


def get_adjacent_matrix(L, num_labels, num_packages):
    adjacent_matrix = np.zeros((num_labels, num_packages))

    for i in range(len(L)):
        adjacent_matrix[L[i].item()][i] = 1

    return adjacent_matrix
