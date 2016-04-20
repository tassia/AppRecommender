from os import path

from src.config import Config
import src.data_classification as data_cl

from utils import sample_classification
import pkg_time

import apt
import calendar
import nltk
import pickle
import re
import time
import xapian

from nltk.stem.snowball import SnowballStemmer


class FilterTag():

    def __init__(self, valid_tags=[]):
        self.valid_tags = valid_tags

    def __call__(self, tag):
        if len(self.valid_tags) == 0:
            return True

        return tag in self.valid_tags


class FilterTerms():

    def __init__(self):
        data_cl.generate_all_terms_tfidf()
        tfidf_weights = data_cl.user_tfidf_weights
        self.tfidf_threshold = sum(tfidf_weights.values()) / len(tfidf_weights)

    def __call__(self, term, used_terms):
        if not (term.islower() or term.startswith("Z")):
            return False

        tfidf = data_cl.term_tfidf_weight_on_user(term)
        return (tfidf > self.tfidf_threshold and len(term) >= 4 and
                self.term_not_used(used_terms, term))

    def term_not_used(self, used_terms, term):
        is_used = term in used_terms
        is_used |= ("Z" + term) in used_terms
        is_used |= term[1:] in used_terms
        return not is_used


class MachineLearningData():

    XAPIAN_DATABASE_PATH = path.expanduser(
        '~/.app-recommender/axi_desktopapps/')
    USER_DATA_DIR = Config().user_data_dir
    BASE_DIR = Config().base_dir

    PKG_DATA_PATH = USER_DATA_DIR + 'pkg_data.txt'

    PKGS_CLASSIFICATIONS = USER_DATA_DIR + 'pkgs_classifications.txt'
    MACHINE_LEARNING_TERMS = USER_DATA_DIR + 'machine_learning_terms.txt'
    MACHINE_LEARNING_DEBTAGS = USER_DATA_DIR + 'machine_learning_debtags.txt'
    MACHINE_LEARNING_TRAINING = USER_DATA_DIR + 'machine_learning_training.txt'

    def __init__(self):
        self.axi = xapian.Database(MachineLearningData.XAPIAN_DATABASE_PATH)
        self.stemmer = SnowballStemmer('english')

    def create_data(self, labels, thresholds):
        if path.isfile(MachineLearningData.PKGS_CLASSIFICATIONS):
            with open(MachineLearningData.PKGS_CLASSIFICATIONS, 'rb') as pkgs:
                return pickle.load(pkgs)

        pkgs = self.get_pkgs_classification(data_cl.square_percent_function,
                                            sample_classification, labels,
                                            thresholds)

        cache = apt.Cache()

        terms_name = self.get_terms_for_all_pkgs(cache, pkgs.keys())
        debtags_name = self.get_debtags_for_all_pkgs(self.axi, pkgs.keys())

        debtags_name = self.filter_debtags(debtags_name)
        debtags_name = sorted(debtags_name)
        terms_name = self.filter_terms(terms_name)
        if len(debtags_name) > 0:
            terms_name = terms_name[0:len(debtags_name)]
        terms_name = sorted(terms_name)

        pkgs_classifications = (
            self.get_pkgs_table_classification(self.axi, pkgs,
                                               cache, debtags_name,
                                               terms_name))

        self.save_pkg_data(terms_name,
                           MachineLearningData.MACHINE_LEARNING_TERMS)

        self.save_pkg_data(debtags_name,
                           MachineLearningData.MACHINE_LEARNING_DEBTAGS)

        self.save_pkg_data(pkgs_classifications,
                           MachineLearningData.PKGS_CLASSIFICATIONS)

        return pkgs_classifications

    def get_pkgs_classification(self, percent_function,
                                classification_function, labels, thresholds):
        pkgs = {}
        time_now = calendar.timegm(time.gmtime())

        pkg_data = pkg_time.get_package_data()

        for name, time_values in pkg_data.iteritems():
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

    def get_pkg_terms(self, cache, pkg_name):
        description = cache[pkg_name].versions[0].description.strip()

        tokens = [word for sent in nltk.sent_tokenize(description) for word in
                  nltk.word_tokenize(sent)]
        filtered_tokens = []

        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        stems = [self.stemmer.stem(t) for t in filtered_tokens]

        return stems

    def get_debtags_name(self, file_path):
        with open(file_path, 'r') as text:
            debtags_name = [debtag.strip() for debtag in text]

        return debtags_name

    def create_row_table_list(self, labels_name, pkg_elements):
        row_list = []

        for debtag in labels_name:
            row_list.append(1 if debtag in pkg_elements else 0)

        return row_list

    def get_terms_for_all_pkgs(self, cache, pkgs):
        pkg_terms = set()
        for pkg in pkgs:
            pkg_terms = pkg_terms | set(self.get_pkg_terms(cache, pkg))

        return pkg_terms

    def get_debtags_for_all_pkgs(self, axi, pkgs):
        pkg_debtags = set()
        for pkg in pkgs:
            pkg_debtags = pkg_debtags | set(self.get_pkg_debtags(axi, pkg))

        return pkg_debtags

    def filter_terms(self, terms):
        term_tfidf = {}
        filtered_terms = []
        content_filter = FilterTerms()
        for term in terms:
            if content_filter(term, filtered_terms):
                term_tfidf[term] = data_cl.term_tfidf_weight_on_user(term)
                filtered_terms.append(term)

        filtered_terms = sorted(term_tfidf.items(), key=lambda term: term[1])
        filtered_terms = [term[0] for term in filtered_terms]

        return filtered_terms

    def filter_debtags(self, debtags):
        valid_tags = []
        filtered_debtags = []
        with open(path.join(Config().filters_dir, "debtags")) as tags:
            valid_tags = [line.strip() for line in tags
                          if not line.startswith("#")]
        content_filter = FilterTag(valid_tags)
        for tag in debtags:
            if content_filter(tag):
                filtered_debtags.append(tag)

        return filtered_debtags

    def get_pkgs_table_classification(self, axi, pkgs, cache,
                                      debtags_name, terms_name):
        pkgs_classification = {}

        for key, value in pkgs.iteritems():

            pkgs_classification[key] = []

            debtags = self.get_pkg_debtags(axi, key)
            debtags = self.create_row_table_list(debtags_name, debtags)
            pkgs_classification[key].extend(debtags)

            terms = self.get_pkg_terms(cache, key)
            terms = self.create_row_table_list(list(terms_name), terms)
            pkgs_classification[key].extend(terms)

            pkgs_classification[key].append(value)

        return pkgs_classification

    def save_pkg_data(self, pkg_data, file_path):
        with open(file_path, 'wb') as text:
            pickle.dump(pkg_data, text)
