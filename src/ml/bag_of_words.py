import pickle

from apt import Cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import GaussianNB

from src.config import Config
from src.ml.data import MachineLearningData


class BagOfWords():

    USER_DATA_DIR = Config().user_data_dir
    BAG_OF_WORDS_MODEL = USER_DATA_DIR + 'bag_of_words_model.pickle'

    MODEL_ALREADY_CREATED = 1
    CREATED_MODEL = 0

    @staticmethod
    def save(bag_of_words, file_path):
        with open(file_path, 'wb') as text:
            pickle.dump(bag_of_words, text)

    @staticmethod
    def load(file_path):
        with open(file_path, 'rb') as text:
            bag_of_words = pickle.load(text)

        return bag_of_words

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_df=0.8,
            max_features=5000,
            min_df=3,
            stop_words='english',
            use_idf=True)

    def get_pkgs_classification(self, pkgs_list):
        pkgs_classification = []

        with open(MachineLearningData.PKGS_CLASSIFICATIONS) as pkgs:
            pkgs_data = pickle.load(pkgs)

            for pkg_name in pkgs_list:
                pkgs_classification.append(pkgs_data[pkg_name][-1])

        return pkgs_classification

    def get_pkg_description(self, pkg, cache, ml_data):
        return ml_data.get_pkg_terms(cache, pkg)

    def get_pkg_debtags(self, pkg, axi, ml_data):
        return map(lambda x: x.replace('::', '_'),
                   ml_data.get_pkg_debtags(axi, pkg))

    def get_pkg_section(self, pkg, cache, ml_data):
        return ml_data.get_pkg_section(cache, pkg)

    def combine_pkg_info(self, description, debtags, section):
        description.extend(debtags)
        description.append(section)

        return description

    def prepare_data(self, pkg_list, axi, cache, ml_data):
        pkgs_description = []
        pkgs_classification = []

        for pkg in pkg_list:
            description = self.get_pkg_description(pkg, cache, ml_data)
            debtags = self.get_pkg_debtags(pkg, axi, ml_data)
            section = self.get_pkg_section(pkg, cache, ml_data)

            pkg_data = self.combine_pkg_info(description, debtags, section)
            pkgs_description.append(' '.join(pkg_data))

        pkgs_classification = self.get_pkgs_classification(pkg_list)

        return (pkgs_description, pkgs_classification)

    def train_model(self, pkgs_list, axi):
        cache = Cache()
        ml_data = MachineLearningData()

        pkgs_description, pkg_classification = self.prepare_data(
            pkgs_list, axi, cache, ml_data)
        pkg_features = self.vectorizer.fit_transform(pkgs_description)

        self.classifier = GaussianNB()
        self.classifier.fit(pkg_features.toarray(), pkg_classification)

        return BagOfWords.CREATED_MODEL
