from os import path

from src.config import Config
import src.data_classification as data_cl

from utils import sample_classification
import pkg_time

import calendar
import pickle
import time
import xapian


class MachineLearningData():

    XAPIAN_DATABASE_PATH = path.expanduser(
        '~/.app-recommender/axi_desktopapps/')
    USER_DATA_DIR = Config().user_data_dir
    BASE_DIR = Config().base_dir

    DEBTAGS_PATH = USER_DATA_DIR + 'tags.txt'
    PKG_DATA_PATH = USER_DATA_DIR + 'pkg_data.txt'

    PKGS_CLASSIFICATIONS = USER_DATA_DIR + 'pkgs_classifications.txt'
    PKGS_CLASSIFICATIONS_INDEX = (USER_DATA_DIR +
                                  'pkgs_classifications_indices.txt')
    MACHINE_LEARNING_TRAINING = USER_DATA_DIR + 'machine_learning_training.txt'

    def __init__(self):
        self.axi = xapian.Database(MachineLearningData.XAPIAN_DATABASE_PATH)

    def create_data(self, labels, thresholds):
        pkgs = self.get_pkgs_classification(data_cl.linear_percent_function,
                                            sample_classification, labels,
                                            thresholds)

        debtags_name = self.get_debtags_name(MachineLearningData.DEBTAGS_PATH)
        terms_name = self.get_terms_for_all_pkgs(self.axi, pkgs.keys())
        self.filter_terms(terms_name)
        terms_name = sorted(terms_name)

        pkgs_classifications = (
            self.get_pkgs_table_classification(self.axi, pkgs,
                                               debtags_name,
                                               terms_name))
        pkgs_classifications_index = debtags_name + terms_name

        self.save_pkg_data(pkgs_classifications,
                           MachineLearningData.PKGS_CLASSIFICATIONS)

        self.save_pkg_data(pkgs_classifications_index,
                           MachineLearningData.PKGS_CLASSIFICATIONS_INDEX)

        return pkgs_classifications

    def get_pkgs_classification(percent_function, classification_function,
                                labels, thresholds):
        pkgs = {}
        time_now = calendar.timegm(time.gmtime())

        pkg_data = pkg_time.get_pkg_data()

        for name, time_values in pkg_data.iteritems:
            modify = time_values[0]
            access = time_values[1]

            percent = percent_function(modify, access, time_now)

            pkgs[name] = classification_function(percent * 100, labels,
                                                 thresholds)

        return pkgs

    def get_pkg_data(self, axi, pkg_name, data_type):
        pkg_name = 'XP' + pkg_name

        query = xapian.Query(xapian.Query.OP_OR, [pkg_name])
        enquire = xapian.Enquire(axi)
        enquire.set_query(query)

        mset = enquire.get_mset(0, 10)

        pkg_info = []
        for pkg in mset:
            for term in axi.get_document(pkg.docid).termlist():

                pkg_term = term.term

                if pkg_term.startswith(data_type):
                    pkg_info.append(pkg_term[len(data_type):])
                elif data_type == 'term':
                    if pkg_term.startswith('Z') or pkg_term[0].islower():
                        pkg_info.append(pkg_term)

        return pkg_info

    def get_pkg_debtags(self, axi, pkg_name):
        return self.get_pkg_data(axi, pkg_name, 'XT')

    def get_pkg_terms(self, axi, pkg_name):
        return self.get_pkg_data(axi, pkg_name, 'term')

    def get_debtags_name(self, file_path):
        with open(file_path, 'r') as text:
            debtags_name = [debtag.strip() for debtag in text]

        return debtags_name

    def create_row_table_list(self, labels_name, pkg_elements):
        row_list = []

        for debtag in labels_name:
            row_list.append(1 if debtag in pkg_elements else 0)

        return row_list

    def get_terms_for_all_pkgs(self, axi, pkgs):
        pkg_terms = set()
        for pkg in pkgs:
            pkg_terms = pkg_terms | set(self.get_pkg_terms(axi, pkg))

        return pkg_terms

    def filter_terms(pkg_terms):

        data_cl.generate_all_terms_tfidf()
        tfidf_weights = data_cl.user_tfidf_weights
        tfidf_threshold = sum(tfidf_weights.values()) / len(tfidf_weights)

        for term in pkg_terms.copy():
            tfidf = data_cl.term_tfidf_weight_on_user(term)

            if tfidf <= tfidf_threshold:
                pkg_terms.remove(term)

    def get_pkgs_table_classification(self, axi, pkgs, debtags_name,
                                      terms_name):
        pkgs_classification = {}

        for key, value in pkgs.iteritems():

            pkgs_classification[key] = []

            debtags = self.get_pkg_debtags(axi, key)
            debtags = self.create_row_table_list(debtags_name, debtags)
            pkgs_classification[key].extend(debtags)

            terms = self.get_pkg_terms(axi, key)
            terms = self.create_row_table_list(list(terms_name), terms)
            pkgs_classification[key].extend(terms)

            pkgs_classification[key].append(value)

        return pkgs_classification

    def save_pkg_data(self, pkg_data, file_path):
        with open(file_path, 'wb') as text:
            pickle.dump(pkg_data, text)
