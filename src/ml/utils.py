INVALID_PARAMETERS = -1


def sample_classification(percent, labels, threshold):

    if len(labels) != len(threshold):
        return INVALID_PARAMETERS

    for index, value in enumerate(threshold):
        if percent >= value:
            return labels[index]

    return labels[-1]
