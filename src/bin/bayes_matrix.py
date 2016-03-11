import numpy as np

D = np.matrix("1 0 0 1 1; 0 1 0 1 0; 1 1 1 1 0; 1 0 1 1 1; 0 1 1 0 0; 1 1 1 0 0")
B = np.matrix("0; 1; 2")
L = np.matrix("0; 1; 1; 2; 2; 1")
A = np.matrix("1 0 0 0 0 0; 0 1 1 0 0 1; 0 0 0 1 1 0")
V = np.matrix("1 1 1 0 0")


def convert_classification_on_numbers(classifications):
    numbers = ""
    for i in range(len(classifications)):
        numbers += "{0};".format(i)

    return np.matrix(numbers[0:-1])


def main(attribute_matrix, classifications):
    D = attribute_matrix
    B = convert_classification_on_numbers(classifications)

    get_adjacent_matrix(L, B.shape[0], D.shape[0])

    H = A.dot(np.ones((D.shape[0], 1)))
    PH = H/D.shape[0]

    R = A * D

    DIAG_H = np.diag(np.array(H)[:, 0])
    PR1 = np.linalg.inv(DIAG_H)*R
    PR2 = 1 - PR1

    v_linha = 1 - V

    maior_dim = max(A.shape[0], A.shape[1])

    PR1 = np.eye(PR1.shape[1], PR1.shape[0]) * PR1
    PR2 = np.eye(PR2.shape[1], PR2.shape[0]) * PR2

    PV1 = PR1 * np.diag(np.array(V.T)[:, 0])
    PV2 = PR2 * np.diag(np.array(v_linha.T)[:, 0])

    PV = PV1 + PV2 + 1
    U = np.log(PV).sum(axis=1)

    PH = np.log(PH + 1)
    U = np.eye(B.shape[0], D.shape[1]) * U
    U = np.diag(np.array(PH)[:, 0]) * U

    print U


def get_adjacent_matrix(L, num_labels, num_packages):
    adjacent_matrix = np.zeros((num_labels, num_packages))

    for i in range(len(L)):
        adjacent_matrix[L[i].item()][i] = 1

    print adjacent_matrix

    return adjacent_matrix
