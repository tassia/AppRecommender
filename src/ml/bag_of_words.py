import os
import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import GaussianNB

from src.config import Config


class BagOfWords():

    USER_DATA_DIR = Config().user_data_dir
    BAG_OF_WORDS_MODEL = USER_DATA_DIR + 'bag_of_words_model.pickle'

    MODEL_ALREADY_CREATED = 1
    CREATED_MODEL = 0

    def __init__(self):
        self.vectorizer = CountVectorizer(
            analyzer="word",
            tokenizer=None,
            preprocessor=None,
            stop_words=None,
            max_features=5000)

    def get_description_and_labels(self, pkgs):
        descriptions, labels = [], []

        for description, label in pkgs:
            descriptions.append(description)
            labels.append(label)

        return (descriptions, labels)

    '''
    :param descriptions: A list containing all the pkgs descriptions.
    '''
    def generate_valid_terms(self, descriptions):
        train_data_features = self.vectorizer.fit_transform(descriptions)
        train_data_features = train_data_features.toarray()

        return train_data_features

    '''
    :param pkgs: A list of tuples containg a package description and its
                 associated label.
    '''
    def train_model(self, pkgs):

        if os.path.exists(BagOfWords.BAG_OF_WORDS_MODEL):
            with open(BagOfWords.BAG_OF_WORDS_MODEL, 'ra') as bag_of_words:
                self.classifier = pickle.load(bag_of_words)
                return BagOfWords.MODEL_ALREADY_CREATED

        descriptions, labels = self.get_description_and_labels(pkgs)

        train_data_features = self.generate_valid_terms(descriptions)

        self.classifier = GaussianNB()
        self.classifier.fit(train_data_features, labels)

        with open(BagOfWords.BAG_OF_WORDS_MODEL, 'wa') as bag_of_words:
            pickle.dump(self.classifier, bag_of_words)

        return BagOfWords.CREATED_MODEL
